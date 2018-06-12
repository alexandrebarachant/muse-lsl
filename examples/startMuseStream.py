from muselsl import stream, list_muses

muses = list_muses()

if not muses:
    print('No Muses found')
else:
    stream(muses[0]['address'])

    # Note: Streaming is synchronous, so code here will not execute until the stream has been closed
    print('Stream has ended')
