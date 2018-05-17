from muselsl import stream

muses = stream.list_muses()

if not muses:
    print('No Muses found')
else:
    stream.stream(muses[0]['address'])

    # Note: Streaming is synchronous, so code here will not execute until the stream has been closed
    print('Stream has ended')
