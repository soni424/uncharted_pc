import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher

spec = importlib.util.spec_from_file_location('uncharted_run', ROOT / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class GameFolderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.collection = self.root / 'collection'
        self.separate = self.root / 'U2 日本語'
        for folder in (self.collection, self.separate):
            folder.mkdir()
            (folder / 'eboot.bin').write_bytes(b'fixture')
        self.out = self.root / 'out' / 'eboot'
        self.out.mkdir(parents=True)
        self.linked = self.out / 'boot-linked.bin'
        self.linked.write_bytes(b'cached fixture')
        future = time.time() + 30
        os.utime(self.linked, (future, future))

    def test_switching_folders_reprepares_even_when_executable_is_older(self):
        (self.out / 'source.txt').write_text(str(self.collection / 'eboot.bin'), encoding='utf-8')
        with patch.object(run, 'PORT', self.root), patch.object(run, 'run_script') as script:
            run.prepare(self.collection, 'eboot.bin', self.out)
            script.assert_not_called()
            run.prepare(self.separate, 'eboot.bin', self.out)
            self.assertEqual(script.call_count, 2)
            script.reset_mock()
            run.prepare(self.separate, 'eboot.bin', self.out)
            script.assert_not_called()

    def test_legacy_cache_without_source_is_reprepared(self):
        with patch.object(run, 'PORT', self.root), patch.object(run, 'run_script') as script:
            run.prepare(self.separate, 'eboot.bin', self.out)
            self.assertEqual(script.call_count, 2)

    def test_loadexec_uses_separate_folder_and_keeps_canonical_game_identity(self):
        settings = {**launcher.APP_DEFAULTS, 'game_dir': str(self.collection),
                    'game_dir_u2': str(self.separate), 'fps_limit': '45',
                    'u1_infinite_health': True, 'u2_infinite_ammo': True}
        with patch.object(launcher, 'write_input_ini', return_value=self.root / 'input.ini'):
            env = launcher.game_environment(settings)
        env.update(BB_DATA_DIR=str(self.root), BB_USER_DIR=str(self.root / 'user'),
                   BB_PROBE=str(self.root / 'probe.exe'), BB_EXE='u1')
        (self.root / 'probe.exe').touch()
        commands = []
        selected_cheats = []

        def prepare(folder, exe, out):
            out.mkdir(parents=True, exist_ok=True)

        def execute(command, **kwargs):
            commands.append(command)
            selected_cheats.append(os.environ['BB_CHEATS'])
            if len(commands) == 1:
                (self.root / 'out' / 'loadexec.txt').write_text(
                    '/app0/big2-ps4_Shipping.elf\nargument\n', encoding='utf-8')
                return SimpleNamespace(returncode=run.LOADEXEC_EXIT)
            return SimpleNamespace(returncode=0)

        cwd = Path.cwd()
        try:
            with patch.object(run, 'PORT', self.root), patch.dict(os.environ, env, clear=True), \
                    patch.object(sys, 'argv', ['run.py']), patch.object(run, 'no_console', return_value=0), \
                    patch.object(run, 'prepare', side_effect=prepare) as preparation, \
                    patch.object(run, 'run_script'), patch.object(run.cheats, 'build', return_value=None) as cheats, \
                    patch.object(run.subprocess, 'run', side_effect=execute):
                self.assertEqual(run.main(), 0)
                self.assertEqual(os.environ['BB_EXE'], 'big2-ps4_Shipping.elf')
                self.assertEqual(os.environ['BB_FPS_LIMIT'], '45')
                self.assertEqual(os.environ['PYTHONUTF8'], '1')
                self.assertEqual(cheats.call_args_list[1].args[0], self.separate / 'eboot.bin')
                self.assertEqual(selected_cheats, ['health', 'ammo'])
            self.assertEqual([c[c.index('--app0') + 1] for c in commands],
                             [str(self.collection), str(self.separate)])
            self.assertEqual(preparation.call_args_list[1].args[:2], (self.separate, 'eboot.bin'))
            self.assertEqual(preparation.call_args_list[1].args[2].name, 'big2')
        finally:
            os.chdir(cwd)


class SideButtonTests(unittest.TestCase):
    def test_capture_requires_focus_and_a_new_press(self):
        app = object.__new__(launcher.Launcher)
        app.root = Mock()
        app.capturing = ('cross', 0)
        app.set_key = Mock()
        with patch.object(launcher, 'side_buttons', return_value=(True, False)):
            app.root.focus_displayof.return_value = None
            app.poll_side_buttons((False, False))
            app.set_key.assert_not_called()
            app.root.focus_displayof.return_value = True
            app.poll_side_buttons((True, False))
            app.set_key.assert_not_called()
            app.poll_side_buttons((False, False))
            app.set_key.assert_called_once_with('cross', 0, 'Mouse 4')


if __name__ == '__main__':
    unittest.main()
