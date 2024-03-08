# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Retroarch launcher
#
# Copyright (c) Chrisism <crizizz@gmail.com>
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

# --- AKL packages ---
from akl import settings
from akl.utils import io, kodi
from akl.launchers import LauncherABC


# -------------------------------------------------------------------------------------------------
# Read RetroarchLauncher.md
# -------------------------------------------------------------------------------------------------
class RetroarchLauncher(LauncherABC):
    
    # --------------------------------------------------------------------------------------------
    # Core functions
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str:
        return 'Retroarch Launcher'
    
    def get_launcher_addon_id(self) -> str:
        addon_id = kodi.get_addon_id()
        return addon_id

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _builder_get_wizard(self, wizard):
        logging.debug('RetroarchLauncher::_builder_get_wizard() Starting ...')
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'application',
                                                       'Select the Retroarch application path',
                                                       self._builder_get_retroarch_app_folders)
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the Retroarch path',
                                              0, '', 'files', None, self._builder_user_selected_custom_browsing)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'application', 'Enter path to Retroarch',
                                            None, self._builder_user_selected_to_type_path)
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'retro_config', 'Select the configuration',
                                                       self._builder_get_available_retroarch_configurations)
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'retro_config', 'Select the configuration',
                                              0, '', 'files', None, self._builder_user_selected_custom_browsing)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'retro_config', 'Enter path to configuration',
                                            None, self._builder_user_selected_to_type_path)
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'retro_core_info', 'Select the core',
                                                       self._builder_get_available_retroarch_cores, self._builder_load_selected_core_info)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'retro_core_info', 'Enter path to core file',
                                            self._builder_load_selected_core_info, self._builder_user_selected_custom_browsing)
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
        logging.debug('RetroarchLauncher::_build_pre_wizard_hook() Starting ...')
        return True

    def _build_post_wizard_hook(self):
        logging.debug('RetroarchLauncher::_build_post_wizard_hook() Starting ...')
        core = self.launcher_settings['retro_core_info']
        core_FN = io.FileName(core)
        self.launcher_settings['secname'] = core_FN.getBaseNoExt()
        return super(RetroarchLauncher, self)._build_post_wizard_hook()

    def _builder_get_retroarch_app_folders(self, item_key, launcher):
        options = collections.OrderedDict()
        options['BROWSE'] = 'Browse for Retroarch path'
        options['TYPE'] = 'Enter Retroarch path manually'

        retroarch_dir = settings.getSetting('retroarch_exec_path')
        if retroarch_dir != '':
            # --- All platforms except Android ---
            retroarch_folder = io.FileName(retroarch_dir, isdir=True)
            if retroarch_folder.exists():
                logging.debug(f"Preset Retroarch directory: {retroarch_folder.getPath()}")
                options[retroarch_folder.getPath()] = retroarch_folder.getPath()

        if io.is_android():
            # --- Android ---
            android_retroarch_folders = [
                '/storage/emulated/0/Android/data/com.retroarch/',
                '/data/data/com.retroarch/',
                '/storage/sdcard0/Android/data/com.retroarch/',
                '/data/user/0/com.retroarch'
            ]
            for retroach_folder_path in android_retroarch_folders:
                retroarch_folder = io.FileName(retroach_folder_path)
                if retroarch_folder.exists():
                    logging.debug(f'Preset Retroarch directory: {retroarch_folder.getPath()}')
                    options[retroarch_folder.getPath()] = retroarch_folder.getPath()

        logging.debug('No Retroarch directory preset')
        return options
        
    def _builder_get_available_retroarch_configurations(self, item_key, launcher):
        configs = collections.OrderedDict()
        configs['BROWSE'] = 'Browse for configuration'
        configs['TYPE'] = 'Enter configuration path manually'

        retroarch_folders: typing.List[io.FileName] = []
        retroarch_folders.append(io.FileName(launcher['application']))

        if io.is_android():
            retroarch_folders.append(io.FileName('/storage/emulated/0/Android/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/data/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/storage/sdcard0/Android/data/com.retroarch/'))
            retroarch_folders.append(io.FileName('/data/user/0/com.retroarch/'))
            retroarch_folders.append(io.FileName('/storage/emulated/0/Retroarch/'))

        for retroarch_folder in retroarch_folders:
            logging.debug(f"scanning path '{retroarch_folder.getPath()}'")
            files = retroarch_folder.recursiveScanFilesInPath('*.cfg')
            if len(files) == 0: 
                continue
            for file in files:
                logging.debug(f"adding config file '{file.getPath()}'")
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
            logging.warning(f'Retroarch config file not found: {config_file.getPath()}')
            kodi.notify_error(f'Retroarch config file not found {config_file.getPath()}. Change path first.')
            return cores_sorted

        parent_dir = io.FileName(config_file.getDir())
        configuration = config_file.readPropertyFile()

        info_folder = self._create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
        cores_folder = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        logging.debug(f"scanning path '{cores_folder.getPath()}'")

        if not info_folder.exists():
            logging.warning('Retroarch info folder not found {}'.format(info_folder.getPath()))
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
            logging.debug(f"get_available_retroarch_cores() adding core using info '{info_file.getPath()}'")

            # check if core exists, if android just skip and guess it exists
            if not io.is_android():
                core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
                if not core_file.exists():
                    logging.warning((f'get_available_retroarch_cores() Cannot find "{core_file.getPath()}". '
                                    f'Skipping info "{info_file.getBase()}"'))
                    continue
                logging.debug(f"get_available_retroarch_cores() using core '{core_file.getPath()}'")
                
            core_info = info_file.readPropertyFile()
            if 'display_name' in core_info:
                cores[info_file.getPath()] = core_info['display_name']
            else:
                logging.warning(f'Cannot read display name for core {info_file.getBaseNoExt()}')
                cores[info_file.getPath()] = info_file.getBaseNoExt()
                
        cores_sorted['BROWSE'] = 'Manual enter path to core'        
        for core_item in sorted(cores.items(), key=lambda x: x[1]):
            cores_sorted[core_item[0]] = core_item[1]
        return cores_sorted

    def _builder_load_selected_core_info(self, input: str, item_key, launchers_settings):
        if input == 'BROWSE':
            return input

        if io.is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        if input.endswith(cores_ext):
            core_file = io.FileName(input)
            launchers_settings['retro_core'] = core_file.getPath()
            return input

        config_file = io.FileName(launchers_settings['retro_config'])
        parent_dir = io.FileName(config_file.getDir())
        configuration = config_file.readPropertyFile()
        cores_folder = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        info_file = io.FileName(input)
        
        core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
        core_info = info_file.readPropertyFile()
        
        launchers_settings[item_key] = info_file.getPath()
        launchers_settings['retro_core'] = core_file.getPath()
                
        launchers_settings['romcollection'] = {}
        launchers_settings['romcollection']['platform'] = core_info['systemname']
        launchers_settings['romcollection']['m_developer'] = core_info['manufacturer']
        launchers_settings['romcollection']['m_name'] = core_info['systemname']

        launchers_settings['scanners'] = {}
        launchers_settings['scanners']['romext'] = core_info['supported_extensions']
        
        return input

    def _builder_user_selected_to_type_path(self, item_key, launcher):
        if launcher[item_key] == 'TYPE':
            launcher[item_key] = ''
            return True
        return False

    def _builder_get_edit_options(self) -> dict:
        options = super()._builder_get_edit_options()
        options[self._change_retroarch_path] = f"Change Retroarch path ({self.launcher_settings['application']})"
        options[self._change_config] = f"Change config: '{self.launcher_settings['retro_config']}'"
        options[self._change_core] = f"Change core: '{self.launcher_settings['retro_core']}'"
        options[self._change_launcher_arguments] = f"Modify Arguments: '{self.launcher_settings['args']}'"
        return options
    
    def _change_retroarch_path(self):
        current_application = self.launcher_settings['application']
        selected_application = kodi.browse(0, 'Select the Retroarch App path', 'files',
                                           '', False, False, current_application)

        if selected_application is None or selected_application == current_application:
            return
        
        self.launcher_settings['application'] = selected_application
        
    def _change_config(self, config_path):
        options = self._builder_get_available_retroarch_configurations('retro_config', self.launcher_settings)
        dialog = kodi.OrdDictionaryDialog()
        
        selected_option = dialog.select('Select Retroarch config', options)
            
        if selected_option is None:
            logging.debug('_change_config(): Selected option = NONE')
            return
                
        logging.debug(f'_change_config(): Selected option = {selected_option}')
        self.launcher_settings['retro_config'] = selected_option

    def _change_core(self):
        options = self._builder_get_available_retroarch_cores('retro_core_info', self.launcher_settings)
        dialog = kodi.OrdDictionaryDialog()
    
        selected_option = dialog.select('Select Retroach Core', options)
     
        if selected_option is None:
            logging.debug('_change_core(): Selected option = NONE')
            return
                
        logging.debug(f'_change_core(): Selected option = {selected_option}')
        self._builder_load_selected_core_info(selected_option, 'retro_core_info', self.launcher_settings)
            
    def _change_launcher_arguments(self):
        args = self.launcher_settings['args']
        args = kodi.dialog_keyboard('Edit application arguments', text=args)

        if args is None:
            return
        self.launcher_settings['args'] = args
        
    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def get_application(self) -> str:
        application = ''
        if io.is_windows():
            app = io.FileName(self.launcher_settings['application'])
            app = app.append('retroarch.exe')
            return app.getPath()
            
        if io.is_android():
            android_app_path = self.launcher_settings['application']
            android_app = next(s for s in reversed(android_app_path.split('/')) if s)
            #  application = f"{android_app}/.browser.retroactivity.RetroActivityFuture"
            return android_app

        if io.is_linux():
            app = io.FileName(self.launcher_settings['application'])
            return app

        return application

    def get_arguments(self, *args, **kwargs) -> typing.Tuple[list, dict]:
        arguments = list(args)
        if io.is_windows() or io.is_linux():
            arguments.append(f'-L "{self.launcher_settings["retro_core"]}"')
            arguments.append(f'-c "{self.launcher_settings["retro_config"]}"')
            arguments.append('"$rom$"')
            
        if io.is_android():
            kwargs["intent"] = "android.intent.action.MAIN"
            kwargs["category"] = "android.intent.category.LAUNCHER"
            kwargs["flags"] = "270532608"  # FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_RESET_TASK_IF_NEEDED
            kwargs["className"] = "com.retroarch.browser.retroactivity.RetroActivityFuture"

            arguments.append("ROM $rom$")
            arguments.append(f"LIBRETRO {self.launcher_settings['retro_core']}")
            arguments.append(f"CONFIGFILE {self.launcher_settings['retro_config']}")
            arguments.append("REFRESH 60")
            
            # arguments.append(f"IME com.android.inputmethod.latin/.LatinIME")

        return super().get_arguments(*arguments, **kwargs)
    
    # ---------------------------------------------------------------------------------------------
    # Misc methods
    # ---------------------------------------------------------------------------------------------    
    def _create_path_from_retroarch_setting(self, path_from_setting: str, parent_dir: io.FileName):
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

    def _switch_core_to_info_file(self, core_file: io.FileName, info_folder: io.FileName):
        info_file = core_file.changeExtension('info')
   
        if io.is_android():
            info_file = info_folder.pjoin(info_file.getBase().replace('_android', ''))
        else:
            info_file = info_folder.pjoin(info_file.getBase())

        return info_file

    def _switch_info_to_core_file(self, info_file: io.FileName, cores_folder: io.FileName, cores_ext):
        core_file = info_file.changeExtension(cores_ext)
        if io.is_android():
            core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
        else:
            core_file = cores_folder.pjoin(core_file.getBase())

        return core_file
