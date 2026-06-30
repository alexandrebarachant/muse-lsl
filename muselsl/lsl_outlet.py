"""Build pylsl outlets from StreamDescriptor metadata."""

from pylsl import StreamInfo, StreamOutlet

_CHANNEL_TYPE = {
    'EEG': 'EEG',
    'PPG': 'PPG',
    'ACC': 'accelerometer',
    'GYRO': 'gyroscope',
    'OPTICS': 'optics',
}


def build_outlet(descriptor, address):
    """Create a StreamOutlet for one stream descriptor."""
    info = StreamInfo(
        'Muse',
        descriptor.stype,
        descriptor.n_channels,
        descriptor.rate,
        'float32',
        'Muse%s' % address,
    )
    info.desc().append_child_value('manufacturer', 'Muse')
    channels = info.desc().append_child('channels')
    channel_type = _CHANNEL_TYPE.get(descriptor.name, descriptor.stype.lower())
    for label in descriptor.channel_names:
        ch = channels.append_child('channel')
        ch.append_child_value('label', label)
        ch.append_child_value('unit', descriptor.unit)
        ch.append_child_value('type', channel_type)
    return StreamOutlet(info, descriptor.chunk)
