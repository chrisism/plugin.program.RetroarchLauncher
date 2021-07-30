# -*- coding: utf-8 -*-
#
# Retroarch Launcher plugin for AEL
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import argparse
import logging
import json

# --- Kodi stuff ---
import xbmcaddon

# AEL main imports
from ael import settings, constants
from ael.utils import kodilogging, kodi, io
from ael.launchers import ExecutionSettings, get_executor_factory

from resources.lib.launcher import RetroarchLauncher

kodilogging.config() 
logger = logging.getLogger(__name__)


# --- Addon object (used to access settings) ---
addon           = xbmcaddon.Addon()
addon_id        = addon.getAddonInfo('id')
addon_version   = addon.getAddonInfo('version')

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin():
    # --- Some debug stuff for development ---
    logger.info('------------ Called Advanced Emulator Launcher Plugin: Retroarch Launcher ------------')
    logger.info('addon.id         "{}"'.format(addon_id))
    logger.info('addon.version    "{}"'.format(addon_version))
    logger.info('sys.platform     "{}"'.format(sys.platform))
    if io.is_android(): logger.info('OS               "Android"')
    if io.is_windows(): logger.info('OS               "Windows"')
    if io.is_osx():     logger.info('OS               "OSX"')
    if io.is_linux():   logger.info('OS               "Linux"')
    for i in range(len(sys.argv)): logger.info('sys.argv[{}] "{}"'.format(i, sys.argv[i]))

    parser = argparse.ArgumentParser(prog='script.ael.retroarchlauncher')
    parser.add_argument('--cmd', help="Command to execute", choices=['launch', 'scan', 'scrape', 'configure'])
    parser.add_argument('--type',help="Plugin type", choices=['LAUNCHER', 'SCANNER', 'SCRAPER'], default=constants.AddonType.LAUNCHER.name)
    parser.add_argument('--romcollection_id', type=str, help="ROM Collection ID")
    parser.add_argument('--rom_id', type=str, help="ROM ID")
    parser.add_argument('--launcher_id', type=str, help="Launcher configuration ID")
    parser.add_argument('--rom', type=str, help="ROM data dictionary")
    parser.add_argument('--rom_args', type=str)
    parser.add_argument('--settings', type=str)
    parser.add_argument('--is_non_blocking', type=bool, default=False)
    
    try:
        args = parser.parse_args()
    except Exception as ex:
        logger.error('Exception in plugin', exc_info=ex)
        kodi.dialog_OK(text=parser.usage)
        return
    
    if   args.type == constants.AddonType.LAUNCHER.name and args.cmd == 'launch': launch_rom(args)
    elif args.type == constants.AddonType.LAUNCHER.name and args.cmd == 'configure': configure_launcher(args)
    else:
        kodi.dialog_OK(text=parser.format_help())
    
    logger.debug('Advanced Emulator Launcher Plugin:  Retroarch Launcher -> exit')
    
# ---------------------------------------------------------------------------------------------
# Launcher methods.
# ---------------------------------------------------------------------------------------------
# Arguments: --settings (json) --rom_args (json) --is_non_blocking --launcher_id --rom_id
def launch_rom(args):
    logger.debug('Retroarch Launcher: Starting ...')
    launcher_settings   = json.loads(args.settings)
    rom_arguments       = json.loads(args.rom_args)
    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo              = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify  = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking          = True if args.is_non_blocking == 'true' else False
        execution_settings.media_state_action       = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine     = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver      = settings.getSettingAsBool('suspend_screensaver')
        
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists(): report_path.makedirs()    
        report_path = report_path.pjoin('{}-{}.txt'.format(args.launcher_id, args.rom_id))
        
        executor_factory = get_executor_factory(report_path)
        launcher = RetroarchLauncher(executor_factory, execution_settings, launcher_settings)
        launcher.launch(rom_arguments)
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')     

# Arguments: --settings (json) --scanner_id (opt) --romcollection_id --launcher_settings (opt)
def configure_launcher(args):
    logger.debug('Retroarch Launcher: Configuring ...')
    launcher_settings = json.loads(args.settings)    
    launcher = RetroarchLauncher(None, None, launcher_settings)
    if args.launcher_id is None and launcher.build():
        launcher.store_launcher_settings(args.romcollection_id)
        return
    
    if args.launcher_id is not None and launcher.edit():
        launcher.store_launcher_settings(args.romcollection_id, args.launcher_id)
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
    