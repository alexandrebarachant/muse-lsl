from .stream import list_muses
import subprocess
from multiprocessing import Process, Pipe, Queue, Event
from datetime import datetime
from pathlib import Path
from time import time, sleep

muse_macs = {
    "4EB2": "00:55:DA:B7:4E:B2"
}

NUM_PARTICIPANTS_PER_TRAIL = 1

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
        self.streaming_queue = Queue()
        self.streaming_proc = Process(target =stream, name="streaming_proc" ,kwargs={
                "address":self.muse_mac, "ppg_enabled":True,
                "acc_enabled":True, "gyro_enabled":True
                ,"abort": self.streaming_queue})
        self.streaming_proc.start()
    
    def stop_streaming(self, join=True):
        self.streaming_queue.put(True)
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
            })
        self.recording_procs[data_type] = p
        p.start()
    
    def _stop_recording(self, data_type, join=True):
        p = self.recording_procs.pop(data_type, None)
        p.abort()
        if join:
            p.join()
    
    def record_all(self, dejitter, data_types):
        data_path = Path(self.experimental_run.data_root) / Path(f"trail{self.experimental_run.trail_id}") / Path(f"part{self.participant_id}")
        data_path.mkdir(parents=True)
        for t in data_types:
            self._start_recording(data_path / "t.csv",dejitter,t)

    def stop_all_recordings(self, join=True):
        for p in self.recording_procs.values():
            p.abort()
        print(f"abborting {len(self.recording_procs.values())} processes")
        if join:
            for p in self.recording_procs.values():
                p.join()

        self.recording_procs = {}

class ExperimentalRun:
    def __init__(self, data_root ,num_participants, trail_id =None):
        self.num_participants = num_participants
        self.participants = []
        if trail_id is None:
            trail_id = datetime.now().isoformat()
        self.trail_id = trail_id
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        for i in range(self.num_participants):
            tmp = Participant(self, i)
            tmp.get_input()
            self.participants.append(tmp)
        
        for p in self.participants:
            p.start_streaming()
        
        for p in self.participants:
            p.record_all(dejitter=True, data_types=ALL_DATATYPES)
        print("all recording")
        while True:
            try:
                if p.streaming_queue.qsize() and p.streaming_queue.get():
                    print("something went wrong")
                    break
                sleep(1)
            except KeyboardInterrupt:
                break


        for p in self.participants:
            p.stop_streaming()
            print("stopping recordings")
            p.stop_all_recordings()
        
        print("recordings stopped")
        for p in self.participants:
            p.streaming_proc.join()

run = ExperimentalRun(data_root="test_recordings", num_participants=NUM_PARTICIPANTS_PER_TRAIL)
run.start()