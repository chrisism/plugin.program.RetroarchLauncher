# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Base launchers
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import collections
import typing

import xbmcaddon

# --- AEL packages ---
from ael.utils import io, kodi
from ael.settings import *
from ael.executors import *
from ael.launchers import *

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Read RetroarchLauncher.md
# -------------------------------------------------------------------------------------------------
class RetroarchLauncher(LauncherABC):
    
    def __init__(self, 
        executorFactory: ExecutorFactoryABC, 
        execution_settings: ExecutionSettings,
        launcher_settings: dict):
        super(RetroarchLauncher, self).__init__(executorFactory, execution_settings, launcher_settings)

    # --------------------------------------------------------------------------------------------
    # Core functions
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str: return 'Retroarch Launcher'
    
    def get_launcher_addon_id(self) -> str: 
        addon = xbmcaddon.Addon()
        addon_id = addon.getAddonInfo('id')
        return addon_id

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _builder_get_wizard(self, wizard):
        logger.debug('RetroarchLauncher::_builder_get_wizard() Starting ...')
        wizard = kodi.WizardDialog_Dummy(wizard, 'application', self._builder_get_retroarch_app_folder())
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the Retroarch path',
            0, '')
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'retro_config', 'Select the configuration',
            self._builder_get_available_retroarch_configurations)
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'retro_config', 'Select the configuration',
            0, '', None, self._builder_user_selected_custom_browsing)
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'retro_core_info', 'Select the core',
            self._builder_get_available_retroarch_cores, self._builder_load_selected_core_info)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'retro_core_info', 'Enter path to core file',
            self._builder_load_selected_core_info, self._builder_user_selected_custom_browsing)
        wizard = kodi.WizardDialog_Dummy(wizard, 'args', self._builder_get_default_retroarch_arguments())
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Extra application arguments')

        return wizard

    #
    # In all platforms except Android:
    #   1) Check if user has configured the Retroarch executable, cores and system dir.
    #   2) Check if user has configured the Retroarch cores dir.
    #   3) Check if user has configured the Retroarch system dir.
    #
    # In Android:
    #   1) ...
    #
    # If any condition fails abort Retroarch launcher creation.
    #
    def _build_pre_wizard_hook(self):
        logger.debug('RetroarchLauncher::_build_pre_wizard_hook() Starting ...')
        return True

    def _build_post_wizard_hook(self):
        logger.debug('RetroarchLauncher::_build_post_wizard_hook() Starting ...')
        core = self.launcher_settings['retro_core_info']
        core_FN = io.FileName(core)        
        self.launcher_settings['secname'] = core_FN.getBaseNoExt()
        return super(RetroarchLauncher, self)._build_post_wizard_hook()

    def _builder_get_retroarch_app_folder(self):

        retroarch_dir = getSetting('retroarch_system_dir')
        if retroarch_dir != '':        
            # --- All platforms except Android ---
            retroarch_folder = io.FileName(retroarch_dir, isdir = True)
            if retroarch_folder.exists():
                logger.debug('Preset Retroarch directory: {}'.format(retroarch_folder.getPath()))
                return retroarch_folder.getPath()

        if io.is_android():
            # --- Android ---
            android_retroarch_folders = [
                '/storage/emulated/0/Android/data/com.retroarch/',
                '/data/data/com.retroarch/',
                '/storage/sdcard0/Android/data/com.retroarch/',
                '/data/user/0/com.retroarch'
            ]
            for retroach_folder_path in android_retroarch_folders:
                logger.debug('_builder_get_retroarch_app_folder() Android testing dir:{}'.format(retroach_folder_path))
                retroarch_folder = io.FileName(retroach_folder_path)
                if retroarch_folder.exists():
                    logger.debug('Preset Retroarch directory: {}'.format(retroarch_folder.getPath()))
                    return retroarch_folder.getPath()

        logger.debug('No Retroarch directory preset')
        return '/'

    def _builder_get_available_retroarch_configurations(self, item_key, launcher):
        configs = collections.OrderedDict()
        configs['BROWSE'] = 'Browse for configuration'

        retroarch_folders:typing.List[io.FileName] = []
        retroarch_folders.append(io.FileName(launcher['application']))

        if io.is_android():
            retroarch_folders.append(io.FileName('/storage/emulated/0/Android/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/data/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/storage/sdcard0/Android/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/data/user/0/com.retroarch/'))

        for retroarch_folder in retroarch_folders:
            logger.debug("get_available_retroarch_configurations() scanning path '{0}'".format(retroarch_folder.getPath()))
            files = retroarch_folder.recursiveScanFilesInPath('*.cfg')
            if len(files) < 1: continue
            for file in files:
                logger.debug("get_available_retroarch_configurations() adding config file '{0}'".format(file.getPath()))
                configs[file.getPath()] = file.getBaseNoExt()

            return configs

        return configs

    def _builder_get_available_retroarch_cores(self, item_key, launcher):
        cores_sorted = collections.OrderedDict()
        cores_ext = ''

        if io.is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        config_file = io.FileName(launcher['retro_config'])
        if not config_file.exists():
            logger.warning('Retroarch config file not found: {}'.format(config_file.getPath()))
            kodi.notify_error('Retroarch config file not found {}. Change path first.'.format(config_file.getPath()))
            return cores_sorted

        parent_dir    = io.FileName(config_file.getDir())
        configuration = config_file.readPropertyFile()

        info_folder   = self._create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
        cores_folder  = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        logger.debug("get_available_retroarch_cores() scanning path '{0}'".format(cores_folder.getPath()))

        if not info_folder.exists():
            logger.warning('Retroarch info folder not found {}'.format(info_folder.getPath()))
            kodi.notify_error('Retroarch info folder not found {}. Read documentation'.format(info_folder.getPath()))
            return cores_sorted
    
        # scan based on info folder and files since Retroarch on Android has it's core files in 
        # the app folder which is not readable without root privileges. Changing the cores folder
        # will not work since Retroarch won't be able to load cores from a different folder due
        # to security reasons. Changing that setting under Android will only result in a reset 
        # of that value after restarting Retroarch ( https://forums.libretro.com/t/directory-settings-wont-save/12753/3 )
        # So we will scan based on info files (which setting path can be changed) and guess that
        # the core files will be available.
        cores = {}
        files = info_folder.scanFilesInPath('*.info')
        for info_file in files:
            
            if info_file.getBaseNoExt() == '00_example_libretro':
                continue
                
            logger.debug("get_available_retroarch_cores() adding core using info '{0}'".format(info_file.getPath()))    

            # check if core exists, if android just skip and guess it exists
            if not io.is_android():
                core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
                if not core_file.exists():
                    logger.warning('get_available_retroarch_cores() Cannot find "{}". Skipping info "{}"'.format(core_file.getPath(), info_file.getBase()))
                    continue
                logger.debug("get_available_retroarch_cores() using core '{0}'".format(core_file.getPath()))
                
            core_info = info_file.readPropertyFile()
            cores[info_file.getPath()] = core_info['display_name']

        cores_sorted['BROWSE'] = 'Manual enter path to core'        
        for core_item in sorted(cores.items(), key=lambda x: x[1]):
            cores_sorted[core_item[0]] = core_item[1]
        return cores_sorted

    def _builder_load_selected_core_info(self, input:str, item_key, launcher, ask_overwrite=False):
        if input == 'BROWSE':
            return input

        if io.is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        if input.endswith(cores_ext):
            core_file = io.FileName(input)
            launcher['retro_core']  = core_file.getPath()
            return input

        config_file     = io.FileName(launcher['retro_config'])
        parent_dir      = io.FileName(config_file.getDir())
        configuration   = config_file.readPropertyFile()
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        info_file       = io.FileName(input)
        
        core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
        core_info = info_file.readPropertyFile()

        launcher[item_key]      = info_file.getPath()
        launcher['retro_core']  = core_file.getPath()
        
        if ask_overwrite and not kodi.dialog_yesno('Do you also want to overwrite previous settings for platform, developer etc.'):
            return input
        
        launcher['romext']      = core_info['supported_extensions']
        launcher['platform']    = core_info['systemname']
        launcher['m_developer'] = core_info['manufacturer']
        launcher['m_name']      = core_info['systemname']

        return input

    def _builder_get_default_retroarch_arguments(self):
        args = ''
        if io.is_android():
            args += '-e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60'

        return args
    
    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def get_application(self) -> str:
        application = ''
        if io.is_windows():
            app = io.FileName(self.launcher_settings['application'])
            app = app.append('retroarch.exe') 
            application = app.getPath()
            
        if io.is_android():
            application = '/system/bin/am'

        # TODO other os
        return application

    def get_execution_ready_arguments(self, rom_arguments: dict) -> str:
        arguments = super(RetroarchLauncher, self).get_execution_ready_arguments(rom_arguments)
        execution_arguments = ''
        if io.is_windows() or io.is_linux():
            execution_arguments =  '-L "{}" '.format(self.launcher_settings['retro_core'])
            execution_arguments += '-c "{}" '.format(self.launcher_settings['retro_config'])
            execution_arguments += '"{}"'.format(rom_arguments['file'])
            execution_arguments += arguments

        if io.is_android():
            android_app_path = self.launcher_settings['application']
            android_app = next(s for s in reversed(android_app_path.split('/')) if s)

            execution_arguments =  'start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER '

            execution_arguments += '-n {}/com.retroarch.browser.retroactivity.RetroActivityFuture '.format(android_app)
            execution_arguments += '-e ROM \'{}\' '.format(rom_arguments['file'])
            execution_arguments += '-e LIBRETRO {} '.format(self.launcher_settings['retro_core'])
            execution_arguments += '-e CONFIGFILE {} '.format(self.launcher_settings['retro_config'])
            execution_arguments += arguments
        
        # TODO: other OSes        
        return execution_arguments
    
    # ---------------------------------------------------------------------------------------------
    # Misc methods
    # ---------------------------------------------------------------------------------------------    
    def _create_path_from_retroarch_setting(self, path_from_setting:str, parent_dir:io.FileName):
        if path_from_setting.startswith(':\\'):
            path_from_setting = path_from_setting[2:]
            return parent_dir.pjoin(path_from_setting, isdir=True)
        else:
            folder = io.FileName(path_from_setting, isdir=True)
            # if '/data/user/0/' in folder.getPath():
            #     alternative_folder = folder.getPath()
            #     alternative_folder = alternative_folder.replace('/data/user/0/', '/data/data/')
            #     folder = FileName(alternative_folder, isdir=True)
            return folder

    def _switch_core_to_info_file(self, core_file, info_folder:io.FileName):
        info_file = core_file.changeExtension('info')
   
        if io.is_android():
            info_file = info_folder.pjoin(info_file.getBase().replace('_android', ''))
        else:
            info_file = info_folder.pjoin(info_file.getBase())

        return info_file

    def _switch_info_to_core_file(self, info_file, cores_folder, cores_ext):
        core_file = info_file.changeExtension(cores_ext)
        if io.is_android():
            core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
        else:
            core_file = cores_folder.pjoin(core_file.getBase())

        return core_file
