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
    parser.add_argument('--server_host', type=str, help="Host")
    parser.add_argument('--server_port', type=int, help="Port")
    parser.add_argument('--rom_id', type=str, help="ROM ID")
    parser.add_argument('--romcollection_id', type=str, help="ROM Collection ID")
    parser.add_argument('--ael_addon_id', type=str, help="Addon configuration ID")
    parser.add_argument('--settings', type=json.loads, help="Specific run setting")
    
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
    
    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo              = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify  = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking          = settings.getSettingAsBool('is_non_blocking')
        execution_settings.media_state_action       = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine     = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver      = settings.getSettingAsBool('suspend_screensaver')
        
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists(): report_path.makedirs()    
        report_path = report_path.pjoin('{}-{}.txt'.format(args.ael_addon_id, args.rom_id))
        
        executor_factory = get_executor_factory(report_path)
        launcher = RetroarchLauncher(
            args.ael_addon_id, 
            args.romcollection_id, 
            args.rom_id, 
            args.server_host, 
            args.server_port,
            executor_factory, 
            execution_settings)
        
        launcher.launch()
        
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')     

# Arguments: --settings (json) --scanner_id (opt) --romcollection_id --launcher_settings (opt)
def configure_launcher(args):
    logger.debug('Retroarch Launcher: Configuring ...')
    
    launcher = RetroarchLauncher(
            args.ael_addon_id, 
            args.romcollection_id, 
            args.rom_id, 
            args.server_host, 
            args.server_port)
        
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
    