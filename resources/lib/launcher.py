# -------------------------------------------------------------------------------------------------
# Read RetroarchLauncher.md
# -------------------------------------------------------------------------------------------------
class RetroarchLauncher(StandardRomLauncher):
    #
    # Handle in this constructor the creation of a new empty ROM Launcher.
    # Concrete classes are responsible of creating a default entity_data dictionary
    # with sensible defaults.
    #
    def __init__(self, PATHS, settings, launcher_dic, objectRepository,
                 executorFactory, romsetRepository, statsStrategy):
        if launcher_dic is None:
            launcher_dic = fs_new_launcher()
            launcher_dic['id'] = misc_generate_random_SID()
            launcher_dic['type'] = OBJ_LAUNCHER_RETROARCH
        super(RetroarchLauncher, self).__init__(
            PATHS, settings, launcher_dic, objectRepository, executorFactory, romsetRepository, statsStrategy
        )

    # --------------------------------------------------------------------------------------------
    # Core functions
    # --------------------------------------------------------------------------------------------
    def get_object_name(self): return 'Retroarch launcher'

    def get_assets_kind(self): return KIND_ASSET_LAUNCHER

    def get_launcher_type(self): return OBJ_LAUNCHER_RETROARCH

    def save_to_disk(self): self.objectRepository.save_launcher(self.entity_data)

    def delete_from_disk(self):
        # Object becomes invalid after deletion.
        self.objectRepository.delete_launcher(self.entity_data)
        self.entity_data = None
        self.objectRepository = None

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs.
    #
    def _builder_get_wizard(self, wizard):
        log_debug('RetroarchLauncher::_builder_get_wizard() Starting ...')
        wizard = WizardDialog_Dummy(wizard, 'application',
            self._builder_get_retroarch_app_folder(self.settings))
        wizard = WizardDialog_FileBrowse(wizard, 'application', 'Select the Retroarch path',
            0, '')
        wizard = WizardDialog_DictionarySelection(wizard, 'retro_config', 'Select the configuration',
            self._builder_get_available_retroarch_configurations)
        wizard = WizardDialog_FileBrowse(wizard, 'retro_config', 'Select the configuration',
            0, '', None, self._builder_user_selected_custom_browsing)
        wizard = WizardDialog_DictionarySelection(wizard, 'retro_core_info', 'Select the core',
            self._builder_get_available_retroarch_cores, self._builder_load_selected_core_info)
        wizard = WizardDialog_Keyboard(wizard, 'retro_core_info', 'Enter path to core file',
            self._builder_load_selected_core_info, self._builder_user_selected_custom_browsing)
        wizard = WizardDialog_FileBrowse(wizard, 'rompath', 'Select the ROMs path',
            0, '')
        wizard = WizardDialog_Keyboard(wizard, 'romext','Set files extensions, use "|" as separator. (e.g nes|zip)')
        wizard = WizardDialog_Dummy(wizard, 'args',
            self._builder_get_default_retroarch_arguments())
        wizard = WizardDialog_Keyboard(wizard, 'args', 'Extra application arguments')
        wizard = WizardDialog_Keyboard(wizard, 'm_name','Set the title of the launcher',
            self._builder_get_title_from_app_path)
        wizard = WizardDialog_Selection(wizard, 'platform', 'Select the platform',
            AEL_platform_list)
        wizard = WizardDialog_Dummy(wizard, 'assets_path', '',
            self._builder_get_value_from_rompath)
        wizard = WizardDialog_FileBrowse(wizard, 'assets_path', 'Select asset/artwork directory',
            0, '')

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
        log_debug('RetroarchLauncher::_build_pre_wizard_hook() Starting ...')

        return True

    def _build_post_wizard_hook(self):
        log_debug('RetroarchLauncher::_build_post_wizard_hook() Starting ...')

        return super(RetroarchLauncher, self)._build_post_wizard_hook()

    def _builder_get_retroarch_app_folder(self, settings):
        if not is_android():
            # --- All platforms except Android ---
            retroarch_folder = FileName(settings['retroarch_system_dir'], isdir = True)
            if retroarch_folder.exists():
                return retroarch_folder.getPath()

        else:
            # --- Android ---
            android_retroarch_folders = [
                '/storage/emulated/0/Android/data/com.retroarch/',
                '/data/data/com.retroarch/',
                '/storage/sdcard0/Android/data/com.retroarch/',
                '/data/user/0/com.retroarch'
            ]
            for retroach_folder_path in android_retroarch_folders:
                retroarch_folder = FileName(retroach_folder_path)
                if retroarch_folder.exists():
                    return retroarch_folder.getPath()

        return '/'

    def _builder_get_available_retroarch_configurations(self, item_key, launcher):
        configs = collections.OrderedDict()
        configs['BROWSE'] = 'Browse for configuration'

        retroarch_folders = []
        retroarch_folders.append(FileName(launcher['application']))

        if is_android():
            retroarch_folders.append(FileName('/storage/emulated/0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileName('/data/data/com.retroarch/'))
            retroarch_folders.append(FileName('/storage/sdcard0/Android/data/com.retroarch/'))
            retroarch_folders.append(FileName('/data/user/0/com.retroarch/'))

        for retroarch_folder in retroarch_folders:
            log_debug("get_available_retroarch_configurations() scanning path '{0}'".format(retroarch_folder.getPath()))
            files = retroarch_folder.recursiveScanFilesInPath('*.cfg')
            if len(files) < 1: continue
            for file in files:
                log_debug("get_available_retroarch_configurations() adding config file '{0}'".format(file.getPath()))
                configs[file.getPath()] = file.getBaseNoExt()

            return configs

        return configs

    def _builder_get_available_retroarch_cores(self, item_key, launcher):
        cores_sorted = collections.OrderedDict()
        cores_ext = ''

        if is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        config_file   = FileName(launcher['retro_config'])

        if not config_file.exists():
            log_warning('Retroarch config file not found: {}'.format(config_file.getPath()))
            kodi_notify_error('Retroarch config file not found {}. Change path first.'.format(config_file.getPath()))
            return cores_sorted

        parent_dir    = FileName(config_file.getDir())
        configuration = config_file.readPropertyFile()
        info_folder   = self._create_path_from_retroarch_setting(configuration['libretro_info_path'], parent_dir)
        cores_folder  = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        log_debug("get_available_retroarch_cores() scanning path '{0}'".format(cores_folder.getPath()))

        if not info_folder.exists():
            log_warning('Retroarch info folder not found {}'.format(info_folder.getPath()))
            kodi_notify_error('Retroarch info folder not found {}. Read documentation'.format(info_folder.getPath()))
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
                
            log_debug("get_available_retroarch_cores() adding core using info '{0}'".format(info_file.getPath()))    

            # check if core exists, if android just skip and guess it exists
            if not is_android():
                core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
                if not core_file.exists():
                    log_warning('get_available_retroarch_cores() Cannot find "{}". Skipping info "{}"'.format(core_file.getPath(), info_file.getBase()))
                    continue
                log_debug("get_available_retroarch_cores() using core '{0}'".format(core_file.getPath()))
                
            core_info = info_file.readPropertyFile()
            cores[info_file.getPath()] = core_info['display_name']

        cores_sorted['BROWSE'] = 'Manual enter path to core'        
        for core_item in sorted(cores.items(), key=lambda x: x[1]):
            cores_sorted[core_item[0]] = core_item[1]
        return cores_sorted

    def _builder_load_selected_core_info(self, input, item_key, launcher, ask_overwrite=False):
        if input == 'BROWSE':
            return input

        if is_windows():
            cores_ext = 'dll'
        else:
            cores_ext = 'so'

        if input.endswith(cores_ext):
            core_file = FileName(input)
            launcher['retro_core']  = core_file.getPath()
            return input

        config_file     = FileName(launcher['retro_config'])
        parent_dir      = FileName(config_file.getDir())
        configuration   = config_file.readPropertyFile()
        cores_folder    = self._create_path_from_retroarch_setting(configuration['libretro_directory'], parent_dir)
        info_file       = FileName(input)
        
        core_file = self._switch_info_to_core_file(info_file, cores_folder, cores_ext)
        core_info = info_file.readPropertyFile()

        launcher[item_key]      = info_file.getPath()
        launcher['retro_core']  = core_file.getPath()
        
        if ask_overwrite and not kodi_dialog_yesno('Do you also want to overwrite previous settings for platform, developer etc.'):
            return input
        
        launcher['romext']      = core_info['supported_extensions']
        launcher['platform']    = core_info['systemname']
        launcher['m_developer'] = core_info['manufacturer']
        launcher['m_name']      = core_info['systemname']

        return input

    def _builder_get_default_retroarch_arguments(self):
        args = ''
        if is_android():
            args += '-e IME com.android.inputmethod.latin/.LatinIME -e REFRESH 60'

        return args

    # --------------------------------------------------------------------------------------------
    # Launcher edit methods
    # --------------------------------------------------------------------------------------------
    def get_main_edit_options(self, category):
        log_debug('RetroarchLauncher::get_main_edit_options() Returning edit options')

        options = collections.OrderedDict()
        options['EDIT_METADATA']          = 'Edit Metadata ...'
        options['EDIT_ASSETS']            = 'Edit Assets/Artwork ...'
        options['EDIT_DEFAULT_ASSETS']    = 'Choose default Assets/Artwork ...'
        options['EDIT_LAUNCHER_CATEGORY'] = "Change Category: '{0}'".format(category.get_name())
        options['EDIT_LAUNCHER_STATUS']   = 'Launcher status: {0}'.format(self.get_finished_str())
        options['LAUNCHER_ADVANCED_MODS'] = 'Advanced Modifications ...'
        options['LAUNCHER_MANAGE_ROMS']   = 'Manage ROMs ...'
        options['LAUNCHER_AUDIT_ROMS']    = 'Audit ROMs / Launcher view mode ...'
        options['EXPORT_LAUNCHER_XML']    = 'Export Launcher XML configuration ...'
        options['DELETE_LAUNCHER']        = 'Delete Launcher'

        return options

    def get_advanced_modification_options(self):
        log_debug('RetroarchLauncher::get_advanced_modification_options() Returning edit options')
        toggle_window_str = 'ON' if self.entity_data['toggle_window'] else 'OFF'
        non_blocking_str  = 'ON' if self.entity_data['non_blocking'] else 'OFF'
        multidisc_str     = 'ON' if self.entity_data['multidisc'] else 'OFF'

        options = collections.OrderedDict()
        options['EDIT_APPLICATION']     = "Change Retroarch App path: '{0}'".format(self.entity_data['application'])
        options['CHANGE_RETROARCH_CONF']= "Change config: '{0}'".format(self.entity_data['retro_config'])
        options['CHANGE_RETROARCH_CORE']= "Change core: '{0}'".format(self.entity_data['retro_core'])
        options['EDIT_ARGS']            = "Modify Arguments: '{0}'".format(self.entity_data['args'])
        options['EDIT_ADDITIONAL_ARGS'] = "Modify aditional arguments ..."
        options['EDIT_ROMPATH']         = "Change ROM path: '{0}'".format(self.entity_data['rompath'])
        options['EDIT_ROMEXT']          = "Modify ROM extensions: '{0}'".format(self.entity_data['romext'])
        options['TOGGLE_WINDOWED']      = "Toggle Kodi into windowed mode (now {0})".format(toggle_window_str)
        options['TOGGLE_NONBLOCKING']   = "Non-blocking launcher (now {0})".format(non_blocking_str)
        options['TOGGLE_MULTIDISC']     = "Multidisc ROM support (now {0})".format(multidisc_str)

        return options

    def get_available_cores(self):
        return self._builder_get_available_retroarch_cores('retro_core_info', self.get_data_dic())
    
    def get_available_configs(self):
        return self._builder_get_available_retroarch_configurations('retro_config', self.get_data_dic())

    def change_application(self):
        current_application = self.entity_data['application']
        selected_application = xbmcgui.Dialog().browse(0, 'Select the Retroarch App path', 'files',
                                                       '', False, False, current_application).decode('utf-8')

        if selected_application is None or selected_application == current_application:
            return False
        self.entity_data['application'] = selected_application

        return True
    
    def change_config(self, config_path):
        self.entity_data['retro_config'] = config_path

    def change_core(self, selected_core_file):
        self._builder_load_selected_core_info(selected_core_file, 'retro_core_info', self.entity_data, True)
    
    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def _launch_selectApplicationToUse(self):
        if is_windows():
            self.application = FileName(self.entity_data['application'])
            self.application = self.application.append('retroarch.exe')  
            return True

        if is_android():
            self.application = FileName('/system/bin/am')
            return True

        # TODO other os
        self.application = ''

        return False

    def _launch_selectArgumentsToUse(self):
        if is_windows() or is_linux():
            self.arguments =  '-L "$retro_core$" '
            self.arguments += '-c "$retro_config$" '
            self.arguments += '"$rom$"'
            self.arguments += self.entity_data['args']
            return True

        if is_android():
            android_app_path = self.entity_data['application']
            android_app = next(s for s in reversed(android_app_path.split('/')) if s)

            self.arguments =  'start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER '

            self.arguments += '-n {}/com.retroarch.browser.retroactivity.RetroActivityFuture '.format(android_app)
            self.arguments += '-e ROM \'$rom$\' '
            self.arguments += '-e LIBRETRO $retro_core$ '
            self.arguments += '-e CONFIGFILE $retro_config$ '
            self.arguments += self.entity_data['args'] if 'args' in self.entity_data else ''
            return True

        # TODO: other OSes
        return False
    
    # ---------------------------------------------------------------------------------------------
    # Misc methods
    # ---------------------------------------------------------------------------------------------    
    def _create_path_from_retroarch_setting(self, path_from_setting, parent_dir):
        if path_from_setting.startswith(':\\'):
            path_from_setting = path_from_setting[2:]
            return parent_dir.pjoin(path_from_setting, isdir=True)
        else:
            folder = FileName(path_from_setting, isdir=True)
            # if '/data/user/0/' in folder.getPath():
            #     alternative_folder = folder.getPath()
            #     alternative_folder = alternative_folder.replace('/data/user/0/', '/data/data/')
            #     folder = FileName(alternative_folder, isdir=True)
            return folder

    def _switch_core_to_info_file(self, core_file, info_folder):
        info_file = core_file.changeExtension('info')
   
        if is_android():
            info_file = info_folder.pjoin(info_file.getBase().replace('_android', ''))
        else:
            info_file = info_folder.pjoin(info_file.getBase())

        return info_file

    def _switch_info_to_core_file(self, info_file, cores_folder, cores_ext):
        core_file = info_file.changeExtension(cores_ext)
        if is_android():
            core_file = cores_folder.pjoin(core_file.getBase().replace('.', '_android.'))
        else:
            core_file = cores_folder.pjoin(core_file.getBase())

        return core_file
