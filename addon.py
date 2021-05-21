# -*- coding: utf-8 -*-
#
# Retroarch Launcher plugin for AEL
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import logging

from resources.lib.utils import kodilogging

kodilogging.config()
logger = logging.getLogger(__name__)

try:
    print('hello')# views.run_plugin(sys.argv)
except Exception as ex:
    #message = text.createError(ex)
    #logger.fatal(message)
    print('error')