from muselsl import muse_stream

muses = muse_stream.list_muses()

if not muses:
    print('No Muses found')
else:
    muse_stream.stream(muses[0]['address'])

    # Note: Streaming is synchronous, so code here will not execute until the stream has been closed
    print('Stream has ended')
