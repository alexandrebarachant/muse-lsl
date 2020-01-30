from .stream import list_muses
import subprocess
from multiprocessing import Process, Pipe, Queue, Event
from datetime import datetime
from pathlib import Path
from time import time, sleep
from .constants import StreamProcMessage

muse_macs = {
    "4EB2": "00:55:DA:B7:4E:B2"
    ,"528C": "00:55:DA:B5:52:8C"
}

NUM_PARTICIPANTS_PER_TRIAL = 2

ALL_DATATYPES=["EEG","PPG","ACC","GYRO"]

muselsl_cli =  ["python3", "-m", "muselsl.__main__"]

class SubProcess():
    def __init__(self, target, kwargs, abort_event, name=None):
        self.process = Process(target=target, kwargs=kwargs,name=name)
        self.abort_event = abort_event
        self.name = name
    
    def start(self):
        self.process.start()

    def abort(self):
        self.abort_event.set()
    
    def join(self):
        return self.process.join()

class Participant:
    def __init__(self, experimental_run, participant_id, muse_id=None, name=None):
        self.experimental_run = experimental_run
        self.participant_id = participant_id
        self.muse_id = muse_id
        self.name = name
        self.muse_mac = muse_macs.get(self.muse_id, None)
        self.streaming_proc = None
        self.recording_procs = {}

    def get_input(self):
        #self.name = input("Name: ")
        while self.muse_mac is None:
            self.muse_id = input(f"[{self.participant_id}]Muse-ID: MUSE-").upper()
            self.muse_mac = muse_macs.get(self.muse_id, None)
        print(f"[{self.participant_id}]Using muse with mac: {self.muse_mac}")

    def start_streaming(self):
        from . import stream
        self.streaming_queue_tx = Queue()
        self.streaming_queue_rx = Queue()
        self.streaming_proc = Process(target =stream, name="streaming_proc" ,kwargs={
                "address":self.muse_mac, "ppg_enabled":True,
                "acc_enabled":True, "gyro_enabled":True
                ,"message_set": self.streaming_queue_rx
                ,"message_get": self.streaming_queue_tx})
        self.streaming_proc.start()
        while self.streaming_queue_rx.empty():
            sleep(0.5)
        return self.streaming_queue_rx.get() == StreamProcMessage.Started
    
    def stop_streaming(self, join=True):
        self.streaming_queue_tx.put(StreamProcMessage.Aborting)
        if join:
            self.streaming_proc.join()

    def _start_recording(self, filename, dejitter, data_type):
        from . import record
        e = Event()
        p = SubProcess(target=record, abort_event=e,name=f"{data_type}_recording_proc"
                ,kwargs={
                "duration": None
                ,"filename":filename
                ,"dejitter":dejitter
                ,"data_source":data_type
                ,"abort":e
                ,"source_id": self.muse_mac
            })
        self.recording_procs[data_type] = p
        p.start()
    
    def _stop_recording(self, data_type, join=True):
        p = self.recording_procs.pop(data_type, None)
        p.abort()
        if join:
            p.join()
    
    def record_all(self, dejitter, data_types):
        data_path = Path(self.experimental_run.data_root) / Path(f"trial{self.experimental_run.trial_id}") / Path(f"part{self.participant_id}")
        data_path.mkdir(parents=True)
        for t in data_types:
            self._start_recording(data_path / f"{t}.csv",dejitter,t)

    def stop_all_recordings(self, join=True):
        for p in self.recording_procs.values():
            p.abort()
        print(f"abborting {len(self.recording_procs.values())} processes")
        if join:
            for p in self.recording_procs.values():
                p.join()

        self.recording_procs = {}

class ExperimentalRun:
    def __init__(self, data_root ,num_participants, trial_id =None):
        self.num_participants = num_participants
        self.participants = []
        if trial_id is None:
            trial_id = datetime.now().isoformat()
        self.trial_id = trial_id
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        for i in range(self.num_participants):
            tmp = Participant(self, i)
            tmp.get_input()
            self.participants.append(tmp)
        
        for p in self.participants:
            success = False
            while not success:
                _ = input("Press any key to try again ...")
                success = p.start_streaming()
                print(f"{'Success' if success else 'Failed'} Started streaming of Part. {p.participant_id}")


        for p in self.participants:
            p.record_all(dejitter=True, data_types=ALL_DATATYPES)
        print("all recording")
        while True:
            try:
                for p in self.participants:
                    if p.streaming_queue_rx.qsize() and p.streaming_queue_rx.get() == StreamProcMessage.Aborting:
                        print("something went wrong")
                        break
                sleep(1)
            except KeyboardInterrupt:
                break


        for p in self.participants:
            print("stopping recordings")
            p.stop_all_recordings()
            print("stopping stream")
            p.stop_streaming()
        
        print("recordings stopped")
        for p in self.participants:
            p.streaming_proc.join()

run = ExperimentalRun(data_root="test_recordings", num_participants=NUM_PARTICIPANTS_PER_TRIAL)
run.start()