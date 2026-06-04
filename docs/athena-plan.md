# Muse S Athena (Gen 3) Support — Implementation Plan

**Status:** Planned, not started. Phase 1 is buildable now without hardware; Phase 2 is hardware-gated.
**Audience:** An implementing agent/engineer with no prior context on this effort.
**Reference implementation:** [brainflow-dev/brainflow#779](https://github.com/brainflow-dev/brainflow/pull/779), commit `7b2e41d3` (local checkout: `/Users/dano/work/brainflow`). Key files:
`src/board_controller/muse/muse_anthena.cpp` (decode), `inc/muse_anthena_constants.h`, `inc/muse_anthena_types.h`, `inc/muse_anthena.h`, `src/utils/inc/custom_cast.h` (bit helpers).
BrainFlow is MIT-licensed; muse-lsl is BSD-3. Porting the decode is license-compatible — **preserve attribution** (cite the PR/commit in `athena.py`).

---

## 1. Goal

Stream from a **Muse S Athena** (a.k.a. Muse S Gen 3) through muse-lsl, starting with EEG and extending to the Athena-only optical/fNIRS sensors. The Athena uses a **fundamentally different BLE protocol** from every prior Muse, so this is a parallel device implementation, not a tweak.

```
LEGACY MUSE (existing muse.py)          ATHENA (new athena.py)
──────────────────────────────         ────────────────────────────────────
EEG = 5 separate characteristics        EEG + IMU + optics + battery ALL
  273e0003..0007 (one per channel)        multiplexed across just TWO chars:
  assembled by hardcoded GATT handle      273e0013 (DATA_1) + 273e0014 (DATA_2)
PPG = 3 chars (273e000f..0011)          one tag-routed parser handles both
12-bit EEG, host-side RLS dejitter      14-bit EEG, 256 kHz device-tick timestamps
```

---

## 2. Protocol Reference (ground truth from BrainFlow `7b2e41d3`)

### 2.1 Service & characteristics

| Role | UUID |
|---|---|
| Service | `0000fe8d-0000-1000-8000-00805f9b34fb` (`0xFE8D`, same Interaxon service) |
| Control (write + notify) | `273e0001-4c4d-454d-96be-f03bac821358` (same UUID as legacy) |
| DATA_1 (notify) | `273e0013-4c4d-454d-96be-f03bac821358` |
| DATA_2 (notify) | `273e0014-4c4d-454d-96be-f03bac821358` |

**Presence of `273e0013` is our Athena discriminator** (Issue 1 / decision 1A). Subscribe to **both** `0013` and `0014`; route to a single parser by packet tag.

### 2.2 Device identification

BrainFlow matches the BLE advertised name by prefix `"MuseS"` (`strncmp(id, "MuseS", 5)`), then relies on the **user selecting** the Athena board id — it does *not* auto-distinguish Athena from the 2021 Muse S. muse-lsl will instead **connect, then probe for `273e0013`** (more robust). Keep a `--model {auto,athena,legacy}` override as an escape hatch.

### 2.3 Command framing (IDENTICAL to muse-lsl `_write_cmd_str`)

```
command bytes = [ len(ascii)+1,  *ascii_bytes,  0x0A ]   written to control char 273e0001
```
muse-lsl's existing `Muse._write_cmd_str()` produces exactly this. Reuse it, but write to the **control characteristic UUID** (not the legacy hardcoded handle `0x000e`).

### 2.4 Init / start / stop sequences (exact, from `prepare_session`/`start_stream`/`stop_stream`)

```
CONNECT (retry up to 3x, 1s apart) → subscribe control 273e0001, DATA_1 0013, DATA_2 0014
INIT (200ms between each):  "v6"  →  "s"  →  "h"  →  <preset>  →  "s"
START:  "dc001"  →(50ms)  "dc001"   [sent twice]
        →(100ms, optional) "L1"     [low-latency, default ON]
        →(300ms) "s" →(200ms)
STOP:   "h"
```
- **Default preset:** `p1041`. Valid presets: `p20 p21 p50 p51 p60 p61 p1034 p1035 p1041 p1042 p1043 p1044 p1045 p1046 p4129`. The preset selects which sensor tags the device emits (must be confirmed empirically — Phase 2).
- `v6` = device info (legacy used `v1`); `s` = status; `h` = halt; `dc001` = begin data; `L1` = low-latency.

### 2.5 Packet structure

A single BLE notification may contain **multiple concatenated packets**. Loop while bytes remain.

```
PACKET  (packet[0] = total length, must be ≥ 14 and ≤ remaining)
┌──────────────────────────── 14-byte PACKET HEADER ───────────────────────────┐
│ [0] len   [1] packet_index   [2..5] device_tick (uint32 LE)   [6..8] (unused) │
│ [9] primary_tag   [10..13] (unused)                                           │
└───────────────────────────────────────────────────────────────────────────────┘
  ├─ PRIMARY payload: parse(primary_tag, packet_index, device_tick,
  │                          data[14 .. 14+data_len], data_len)
  └─ then zero+ SUBPACKETS while ≥ 5 bytes remain:
       ┌── 5-byte SUBPACKET HEADER ──┐
       │ [0] tag  [1] sub_index  [2..4] (unused) │  then data_len payload bytes
       └─────────────────────────────┘
     advance by 5 + data_len
```
`data_len` per tag is fixed (see table), except variable-length battery (`0x88`) consumes the remainder.

### 2.6 Sensor config table (`get_sensor_config`)

| tag | type | channels | samples/pkt | rate (Hz) | payload bytes |
|----|------|----------|-------------|-----------|---------------|
| `0x11` | EEG | 4 | 4 | 256 | 28 |
| `0x12` | EEG | 8 | 2 | 256 | 28 |
| `0x34` | OPTICS | 4 | 3 | 64 | 30 |
| `0x35` | OPTICS | 8 | 2 | 64 | 40 |
| `0x36` | OPTICS | 16 | 1 | 64 | 40 |
| `0x47` | ACC_GYRO | 6 | 3 | 52 | 36 |
| `0x53` | UNKNOWN | – | – | – | 24 (skip) |
| `0x88` | BATTERY | 1 | 1 | 0.2 | variable |
| `0x98` | BATTERY | 1 | 1 | 1.0 | 20 |

### 2.7 Per-sensor decode

**EEG (`0x11` = 4ch×4samp; `0x12` = 8ch×2samp), 14-bit LSB-first, unsigned:**
```
for sample in range(n_samples):
    for channel in range(n_channels):
        bit_start = (sample * n_channels + channel) * 14
        raw   = extract_lsb_bits(data, bit_start, 14)       # 0..16383
        value = raw * (1450.0 / 16383.0)                    # µV; NOTE: no midpoint offset
```
`extract_lsb_bits(data, bit_start, width)` = read `width` bits starting at absolute bit `bit_start`, LSB-first within the little-endian byte stream (port from `custom_cast.h`). 4 EEG channels map to TP9, AF7, AF8, TP10 (the extra 4 in `0x12` are "other" electrodes — defer).

**ACC_GYRO (`0x47` = 6ch×3samp), int16 little-endian:** per sample, 6 × int16 = `[ax,ay,az,gx,gy,gz]`:
```
raw_i16 = int16_le(data[(sample*6 + ch)*2 : +2])
accel = raw_i16 * 0.0000610352          # ch 0..2
gyro  = raw_i16 * -0.0074768            # ch 3..5  (NOTE: NEGATIVE scale; legacy was +)
```

**OPTICS (`0x34/0x35/0x36`), 20-bit LSB-first, unsigned:**
```
bit_start = (sample*n_channels + channel) * 20
raw   = extract_lsb_bits(data, bit_start, 20)
value = raw * 1.0
canonical_index = optics_index(tag, channel)   # 0x34→{4,5,6,7}; 0x35→0..7; 0x36→0..15
```

**BATTERY (`0x88`/`0x98`):** `battery = uint16_le(data[0:2]) / 256.0` (percent). Cached; BrainFlow attaches it to optics packets.

### 2.8 Timestamps (device-clock, NOT RLS)

```
on first packet:  t0_tick = device_tick;  t0_host = host_now()
sample_ts = t0_host + (device_tick - t0_tick)/256000.0 + sample_index/sampling_rate
```
`device_tick` is uint32 → use modular subtraction for wraparound. This **replaces** the RLS dejittering for Athena. (Reset `timestamp_initialized` on every `start_stream`.)

---

## 3. Locked architecture decisions (from plan-eng-review)

| # | Decision | Note after BrainFlow review |
|---|---|---|
| 1 | Route via **GATT capability probe** for `273e0013` (connect-first); clear error if neither legacy nor Athena EEG char present | Confirmed superior to BrainFlow's name-only match |
| 2 | Extract **RLS dejitter as a shared utility** (composition, no inheritance) | **REVISED:** Athena uses device-tick timestamps, so it does NOT consume the RLS util. Extraction is now optional cleanup for legacy only — treat as low priority, not part of the Athena critical path |
| 3 | **Device-driven `StreamDescriptor`** (frozen dataclass); `stream.py` builds outlets generically; legacy `Muse` also exposes descriptors via the single path (regression-tested unchanged) | Athena descriptors: EEG 4ch@256, ACC@52, GYRO@52, OPTICS@64, plus battery |
| 4 | Athena **duplicates** its own subscribe block; no shared subscribe helper | – |
| 5 | `StreamDescriptor` = **frozen dataclass** (name, stype, n_channels, channel_names, rate, chunk, unit) | – |
| 6 | **Add pytest + `tests/` + CI** this PR (project currently has zero tests) | Decode is pure functions → highly testable |
| 7 | Decode fixtures = **captured from a real Athena** (raw bytes → expected values) | Hardware-gated → Phase 2 |
| 8 | Decode with **bitstring** to match muse.py style + a hot-path **benchmark**; numpy only if proven slow | `extract_lsb_bits` 14/20-bit maps cleanly to bitstring |

---

## 4. Phase 1 — buildable NOW (no hardware), file by file

1. **`muselsl/constants.py`** — add Athena block: `MUSE_ANTHENA_GATT_DATA_1/2`, control UUID, sensor-config table (tag→(type,ch,samp,rate,bytes)), scale factors (`EEG=1450/16383`, `ACC=0.0000610352`, `GYRO=-0.0074768`, `OPTICS=1.0`), `DEVICE_CLOCK_HZ=256000.0`, valid presets, default `p1041`, header sizes (14, 5).

2. **`muselsl/athena.py`** (new) — `Athena` class. Same callback contract as `Muse` (`callback_eeg/acc/gyro/ppg`/optics). Methods: `connect()` (subscribe control + 0013 + 0014; **mandatory inline ASCII byte-layout diagram** above the parser per repo convention), `select_preset()`, `start()`/`stop()` issuing the §2.4 sequences via the reused `_write_cmd_str` framing, `_handle_data()` → packet loop → `_parse_payload(tag, seq, tick, data)` dispatch → per-sensor decoders (§2.7), `_sample_timestamp()` (§2.8). Decoders are **pure module-level functions** (`decode_eeg(bytes)->ndarray`, etc.) so they're unit-testable without BLE. Cite BrainFlow PR #779 in the module docstring.

3. **`muselsl/devices.py`** (new, small) — `create_device(address, ...)` factory: connect → probe for `273e0013` → return `Athena` else `Muse`; raise a clear `RuntimeError` if neither EEG characteristic exists. Honor a `model` override. **Inline ASCII decision-tree diagram.**

4. **`muselsl/stream.py`** — replace the hardcoded `StreamInfo`/`StreamOutlet` blocks (currently lines ~165-219) with a generic builder that loops over `device.stream_descriptors()`. Route construction through `create_device(...)` instead of `Muse(...)` directly (lines 232 & 271). The push closure (lines 221-228) stays.

5. **`muselsl/cli.py`** — add `--model {auto,athena,legacy}` to the relevant subcommands; thread through to `stream()`.

6. **`muselsl/muse.py`** — `Muse` grows a `stream_descriptors()` returning descriptors matching today's hardcoded shapes (EEG 5ch@256 names `TP9,AF7,AF8,TP10,Right AUX`; PPG 3@64; ACC/GYRO 3@52). Behavior must be **identical** — covered by regression test.

7. **`tests/`** (new) + wire pytest into `tox.ini` (drop py27/py36) + a CI job.

### Stream descriptor (decision 5)
```python
@dataclass(frozen=True)
class StreamDescriptor:
    name: str            # "EEG", "PPG", "ACC", "GYRO", "OPTICS"
    stype: str           # LSL type
    n_channels: int
    channel_names: tuple[str, ...]
    rate: float
    chunk: int
    unit: str
```

---

## 5. Test plan (decision 6; ✗ = write it)

```
[1] factory: probe 273e0013 → Athena / legacy / neither-raises   ✗ test_factory_* (mock services)
[2] EEG decode 14-bit (tag 0x11)                                 ✗ test_athena_eeg_decode  ← @skip until 7A fixtures
[3] ACC_GYRO decode int16, negative gyro scale (0x47)            ✗ test_athena_accgyro_decode ← @skip
[4] OPTICS decode 20-bit + canonical index (0x34/35/36)          ✗ test_athena_optics_decode  ← @skip
[5] packet framing: multi-packet, primary + subpackets, bad len  ✗ test_athena_packet_split (synthetic bytes OK)
[6] device-tick timestamp + uint32 wraparound                    ✗ test_athena_timestamp
[7] command framing: v6/s/h/preset/dc001/L1 exact bytes          ✗ test_athena_commands
[8] StreamDescriptor → outlet (legacy regression + athena)       ✗ test_descriptors_*
[9] hot-path decode benchmark (decision 8)                       ✗ bench_athena_decode
```
**Critical:** [2]/[3]/[4] (sample-value correctness) need real ground truth (decision 7A) and are `@pytest.mark.skip(reason="needs Athena capture")` until Phase 2. **Framing [5], timestamp [6], commands [7] do NOT need hardware** — synthetic byte vectors fully exercise them, so write them now. This converts the only silent-corruption risk (wrong bit offsets) into loudly-skipped tests while everything structural is green.

### Failure modes
- Probe on a legacy device must be treated as "not Athena" (signal, not exception) — test [1].
- Wrong bit offset → plausible garbage µV, no runtime check → **silent**; only [2]/[3]/[4] + real fixtures close it.
- `device_tick` wraparound mishandled → timestamp jumps → **silent**; test [6] covers.
- Descriptor refactor reorders/renames legacy channels → silent break for LSL consumers → regression test [8] covers.

---

## 6. Phase 2 — hardware-gated (see `TODOS.md`)
Capture raw `0013`/`0014` packets + BrainFlow-decoded values from a physical Athena → commit fixtures → un-skip [2]/[3]/[4] → validate/correct decoders → run benchmark. Determine which **preset** yields which sensor tags. Then wire optics/fNIRS LSL streams.

## 7. NOT in scope
- Athena 8-channel EEG variant (`0x12`) extra electrodes — defer.
- Optics/fNIRS LSL streams — Phase 3 (after EEG validated).
- Legacy `Muse.connect()` subscribe-block dedup — tracked in `TODOS.md` (decision 4C left legacy untouched).
- Viewer changes — separate web-viewer effort.

## 8. Open questions to resolve on hardware
- Which preset(s) emit tag `0x11` EEG vs the 8-ch `0x12`? Does `p1041` (default) stream EEG+optics+IMU together?
- EEG has **no midpoint offset** in BrainFlow (`raw * scale`). Confirm sign/centering against real signals.
- Bytes `[6..8]` and `[10..13]` of the packet header are unused by BrainFlow — confirm they carry nothing we need.
- Does muse-lsl's `BleakBackend` support write-by-UUID + notify on `0013/0014`? (Legacy path writes to handle `0x000e`.)
```
