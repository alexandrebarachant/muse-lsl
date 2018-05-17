from muselsl import lsl_record

# Note: an existing Python process running a Muse LSL stream is required
lsl_record.record(60)

# Note: Recording is synchronous, so code here will not execute until the stream has been closed
print('Recording has ended')
