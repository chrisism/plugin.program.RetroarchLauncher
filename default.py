# -*- coding: utf-8 -*-
#
# Retroarch Launcher plugin for AKL
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import logging

# --- Kodi stuff ---
import xbmcaddon

# AKL main imports
from akl import settings, addons
from akl.utils import kodilogging, kodi, io
from akl.launchers import ExecutionSettings, get_executor_factory

from resources.lib.launcher import RetroarchLauncher

kodilogging.config()
logger = logging.getLogger(__name__)

# --- Addon object (used to access settings) ---
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')


# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin():
    os_name = io.is_which_os()
    
    # --- Some debug stuff for development ---
    logging.info('------------ Called Advanced Kodi Launcher Plugin: Retroarch Launcher ------------')
    logging.info(f'addon.id         "{addon_id}"')
    logging.info(f'addon.version    "{addon_version}"')
    logging.info(f'sys.platform     "{sys.platform}"')
    logging.info(f'OS               "{os_name}"')
    
    for i in range(len(sys.argv)):
        logging.info(f'sys.argv[{i}] "{sys.argv[i]}"')

    addon_args = addons.AklAddonArguments('script.akl.retroarchlauncher')
    try:
        addon_args.parse()
    except Exception as ex:
        logger.error('Exception in plugin', exc_info=ex)
        kodi.dialog_OK(text=addon_args.get_usage())
        return
    
    if addon_args.get_command() == addons.AklAddonArguments.LAUNCH:
        launch_rom(addon_args)
    elif addon_args.get_command() == addons.AklAddonArguments.CONFIGURE_LAUNCHER:
        configure_launcher(addon_args)
    else:
        kodi.dialog_OK(text=addon_args.get_help())

    logging.debug('Advanced Kodi Launcher Plugin:  Retroarch Launcher -> exit')
    
 
# ---------------------------------------------------------------------------------------------
# Launcher methods.
# ---------------------------------------------------------------------------------------------
# Arguments: --cmd launch --akl_addon_id --rom_id
def launch_rom(args: addons.AklAddonArguments):
    logging.debug('Retroarch Launcher: Starting ...')
    
    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking = settings.getSettingAsBool('is_non_blocking')
        execution_settings.media_state_action = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver = settings.getSettingAsBool('suspend_screensaver')
        execution_settings.suspend_joystick_engine = settings.getSettingAsBool('suspend_joystick')
        
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists():
            report_path.makedirs()
        report_path = report_path.pjoin('{}-{}.txt'.format(args.get_akl_addon_id(), args.get_entity_id()))
        
        executor_factory = get_executor_factory(report_path)
        launcher = RetroarchLauncher(
            args.get_akl_addon_id(),
            args.get_entity_id(),
            args.get_webserver_host(),
            args.get_webserver_port(),
            executor_factory,
            execution_settings)
        
        launcher.launch()
        
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')


# Arguments: --akl_addon_id --rom_id
def configure_launcher(args: addons.AklAddonArguments):
    logger.debug('Retroarch Launcher: Configuring ...')
    
    launcher = RetroarchLauncher(
        args.get_akl_addon_id(),
        args.get_entity_id(),
        args.get_webserver_host(),
        args.get_webserver_port())
        
    if launcher.build():
        launcher.store_settings()
        return
    
    kodi.notify_warn('Cancelled creating launcher')


# ---------------------------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------------------------
try:
    run_plugin()
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")
