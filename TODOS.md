# TODOS

## Athena (Muse S Gen 3) support

### Phase 2: Capture ground-truth fixtures and validate the EEG decoder

**What:** Capture raw `273e0013` EEG packets from a physical Muse S Athena alongside BrainFlow's decoded microvolt output, commit them as test fixtures, un-skip the decode tests, correct the ported decoder against real data, and run the hot-path micro-benchmark.

**Why:** Phase 1 lands the Athena scaffolding (factory/routing, descriptors, command framing) with a decoder ported from [brainflow-dev/brainflow#779](https://github.com/brainflow-dev/brainflow/pull/779) but **unvalidated** — a wrong bit offset would produce plausible-looking EEG-shaped garbage with no runtime check. Real ground truth is the only way to prove the decode is correct.

**Context:** Athena consolidates all EEG channels into a single BLE characteristic (`273e0013`) plus an aux characteristic (`273e0014`), versus legacy Muse's one-characteristic-per-channel model. The Phase 1 decoder lives in `muselsl/athena.py` with an inline ASCII byte-layout diagram and the decode tests are marked `@pytest.mark.skip(reason="needs Athena ground-truth capture")`. Start by recording packets with the LSL/Bleak path while logging BrainFlow's output for the same stream, then turn those into `tests/fixtures/` vectors (raw bytes → expected µV).

**Effort:** M
**Priority:** P1
**Depends on:** Physical Muse S Athena hardware; Phase 1 scaffolding merged.

### Phase 3: Athena aux streams (PPG / IMU / optical-fNIRS)

**What:** Decode the `273e0014` aux characteristic into PPG, accelerometer/gyro, and optical-fNIRS LSL streams, exposed via the `StreamDescriptor` mechanism.

**Why:** The optical/fNIRS sensors are the headline reason Athena is compelling beyond a legacy Muse; EEG-only parity is just the entry point.

**Context:** The Phase 1 `StreamDescriptor` dataclass + generic outlet builder in `stream.py` are designed to make adding new stream shapes additive (no `stream.py` branching). The aux packet format is not yet reverse-engineered — source it from PR #779's changed files and validate with captured fixtures, same approach as Phase 2.

**Effort:** L
**Priority:** P2
**Depends on:** Phase 2 (validated decoder + fixture-capture workflow).

## Legacy / Infrastructure

### Dedupe the subscribe sequence in muse.py `connect()`

**What:** Extract the copy-pasted enable/subscribe block in `Muse.connect()` (`muselsl/muse.py` ~lines 99-124 and again ~138-158 in the `BLEError "characteristic"` retry branch) into a single helper.

**Why:** The full `if enable_eeg/control/telemetry/acc/gyro/ppg → subscribe` sequence is duplicated verbatim, so any change must be made twice — classic drift risk.

**Context:** Deliberately left untouched during the Athena work (review decision 4C) because it sits in the fragile auto-reset/reconnect path that can't be exercised without legacy hardware. Worth doing alongside a legacy-device test pass so the reconnect branch is covered before refactoring.

**Effort:** S
**Priority:** P3
**Depends on:** Access to a legacy Muse for reconnect-path testing.
