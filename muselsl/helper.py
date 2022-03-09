import platform
import warnings


def warn_bluemuse_not_supported(extra_text = ''):
    warnings.warn('Operation not supported by bluemuse backend.' + extra_text,
                  RuntimeWarning)


def resolve_backend(backend):
    if backend == 'auto':
        ## if there are any issues with bleak,
        ## below are the previous defaults
        # platformName = platform.system().lower()
        # if platformName == 'linux' or platformName == 'linux2':
        #     backend = 'gatt'
        # elif platformName == 'windows' and int(platform.version().replace('.', '')) >= 10015063:
        #     backend = 'bluemuse'
        # else:
        #     backend = 'bgapi'
        backend = 'bleak'
    if backend in ['gatt', 'bgapi', 'bluemuse', 'bleak']:
        return backend
    else:
        raise(ValueError('Backend must be one of: auto, gatt, bgapi, bluemuse, bleak.'))
