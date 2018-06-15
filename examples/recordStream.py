from muselsl import record

# Note: an existing Muse LSL stream is required
record(60)

# Note: Recording is synchronous, so code here will not execute until the stream has been closed
print('Recording has ended')
