import logging

logger = logging.getLogger(__name__)


def view(window=5, scale=100, refresh=0.2, figure="15x6", version=1, backend='TkAgg'):
    logger.info('Starting viewer v%d (window=%ss, scale=%suV, refresh=%ss, backend=%s)',
                version, window, scale, refresh, backend)
    if version == 2:
        from . import viewer_v2
        viewer_v2.view()
    else:
        from . import viewer_v1
        viewer_v1.view(window, scale, refresh, figure, backend)
