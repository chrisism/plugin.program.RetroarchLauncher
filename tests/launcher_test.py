import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from fakes import FakeFile, FakeExecutor, random_string

from resources.lib.launcher import RetroarchLauncher
from akl.launchers import ExecutionSettings
from akl.api import ROMObj
from akl.utils import io

class Test_Launcher(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        logger.info('ROOT DIR: {}'.format(cls.ROOT_DIR))
        logger.info('TEST DIR: {}'.format(cls.TEST_DIR))
        logger.info('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        logger.info('---------------------------------------------------------------------------')
    
    @patch('resources.lib.launcher.io.is_windows')
    @patch('resources.lib.launcher.io.is_android')
    @patch('resources.lib.launcher.io.is_linux')    
    @patch('akl.launchers.kodi', autospec=True)
    @patch('akl.utils.io.FileName', side_effect = FakeFile)
    @patch('akl.api.client_get_rom')
    @patch('akl.api.client_get_collection_launcher_settings')
    @patch('akl.executors.ExecutorFactory')
    def test_if_retroarch_launcher_will_apply_the_correct_arguments_when_running_on_android(self, 
            factory_mock:MagicMock, api_settings_mock:MagicMock, api_rom_mock: MagicMock, filename_mock, kodi_mock,
            is_linux_mock:MagicMock,is_android_mock:MagicMock, is_win_mock:MagicMock):
        
        # arrange
        launcher_id     = random_string(10)
        collection_id   = random_string(10)
        rom_id          = random_string(10)

        is_linux_mock.return_value = False
        is_win_mock.return_value = False
        is_android_mock.return_value = True
        
        launcher_settings = {}
        launcher_settings['id'] = 'ABC'
        launcher_settings['toggle_window'] = True
        launcher_settings['romext'] = None
        launcher_settings['args_extra'] = None
        launcher_settings['roms_base_noext'] = 'snes'
        launcher_settings['retro_core'] = '/data/data/com.retroarch/cores/mame_libretro_android.so'
        launcher_settings['retro_config'] = '/storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg'
        launcher_settings['application'] = '/storage/emulated/0/Android/data/com.retroarch/'
        api_settings_mock.return_value = launcher_settings

        mock = FakeExecutor()
        factory_mock.create.return_value = mock
        
        rom = ROMObj({
            'id': rom_id,
            'm_name': 'TestCase',
            'scanned_data': {'file': 'superrom.zip'}
        })
        api_rom_mock.return_value = rom

        expected = '/system/bin/am'
        #expectedArgs = "start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.retroarch/.browser.retroactivity.RetroActivityFuture -e ROM 'superrom.zip' -e LIBRETRO /data/data/com.retroarch/cores/mame_libretro_android.so -e CONFIGFILE /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg "
        expectedArgs = "start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.retroarch/com.retroarch.browser.retroactivity.RetroActivityFuture -e ROM 'superrom.zip' -e LIBRETRO /data/data/com.retroarch/cores/mame_libretro_android.so -e CONFIGFILE /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg "
                 
        # act
        target = RetroarchLauncher(launcher_id, collection_id, None, 'localhost', 8080, factory_mock, ExecutionSettings())
        target.launch()

        # assert
        actual = mock.actualApplication
        actualArgs = mock.actualArgs
        assert actual == expected
        self.assertEqual(expectedArgs, actualArgs)
        

    @patch('resources.lib.launcher.io.is_android')
    @patch('akl.api.client_get_collection_launcher_settings')
    def test_retroarchlauncher_switching_core_to_info_file(self, api_settings_mock:MagicMock, is_android_mock:MagicMock):
        # arrange
        is_android_mock.return_value = True
                        
        info_path = io.FileName('/data/user/0/infos/')
        core_path = io.FileName('/data/user/0/cores/mycore_libretro_android.so')
        
        launcher_settings = {}
        launcher_settings['id'] = 'ABC'
        launcher_settings['toggle_window'] = True
        launcher_settings['romext'] = None
        launcher_settings['args_extra'] = None
        launcher_settings['roms_base_noext'] = 'snes'
        launcher_settings['retro_core'] = core_path.getPath()
        launcher_settings['retro_config'] = '/storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg'
        launcher_settings['application'] = '/storage/emulated/0/Android/data/com.retroarch/'
        api_settings_mock.return_value = launcher_settings
        
        target = RetroarchLauncher(None, random_string(5), None, None, 0, None, None)
                
        # act
        actual = target._switch_core_to_info_file(core_path, info_path)
        
        # assert
        logger.debug(actual.path_tr)
        self.assertIsNotNone(actual)
        self.assertEqual(u'/data/user/0/infos/mycore_libretro.info', actual.path_tr)

if __name__ == '__main__':
   unittest.main()
