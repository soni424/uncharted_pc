import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher


class SaveBackupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.user = self.root / 'user'
        for name in ('savedata', 'trophy', 'cache'):
            (self.user / name).mkdir(parents=True)
            (self.user / name / 'fixture.bin').write_bytes(name.encode())
        self.app = object.__new__(launcher.Launcher)
        self.app.app = {'user_dir': str(self.user)}
        self.app.vars = {}
        self.app.process = None
        self.app.filedialog = Mock()
        self.app.messagebox = Mock()
        self.app.messagebox.askyesno.return_value = True
        self.archive = self.root / 'backup.zip'

    def restore(self, path=None):
        self.app.filedialog.askopenfilename.return_value = str(path or self.archive)
        self.app.import_saves()

    def test_export_restore_and_safety_backup_exclude_shader_cache(self):
        self.app._write_save_archive(self.archive)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertNotIn('cache/fixture.bin', archive.namelist())
        for name in ('savedata', 'trophy'):
            (self.user / name / 'fixture.bin').write_bytes(b'new progress')
        self.restore()
        self.app.messagebox.showerror.assert_not_called()
        for name in ('savedata', 'trophy'):
            self.assertEqual((self.user / name / 'fixture.bin').read_bytes(), name.encode())
        self.assertEqual((self.user / 'cache/fixture.bin').read_bytes(), b'cache')
        backups = list((self.user / 'backups').glob('*.zip'))
        self.assertEqual(len(backups), 1)
        with zipfile.ZipFile(backups[0]) as archive:
            self.assertEqual(archive.read('savedata/fixture.bin'), b'new progress')

    def test_invalid_paths_and_missing_roots_keep_current_saves(self):
        cases = [(['savedata'], '../outside'), (['savedata'], 'savedata/../../outside'),
                 (['savedata'], 'savedata/C:outside'), (['savedata', 'trophy'], 'savedata/new'),
                 (['savedata', 'savedata'], 'savedata/new')]
        for roots, entry in cases:
            with self.subTest(entry=entry, roots=roots):
                self.app.messagebox.reset_mock()
                with zipfile.ZipFile(self.archive, 'w') as archive:
                    archive.writestr('backup_info.json', json.dumps(
                        {'format': 'uncharted-save-backup-v1', 'folders': roots}))
                    archive.writestr(entry, b'new')
                self.restore()
                self.app.messagebox.showerror.assert_called_once()
                self.assertEqual((self.user / 'savedata/fixture.bin').read_bytes(), b'savedata')
                self.assertEqual((self.user / 'trophy/fixture.bin').read_bytes(), b'trophy')
                self.assertFalse((self.root / 'outside').exists())

    def test_corrupt_payload_keeps_current_saves(self):
        self.app._write_save_archive(self.archive)
        with zipfile.ZipFile(self.archive) as archive:
            info = archive.getinfo('savedata/fixture.bin')
        data = bytearray(self.archive.read_bytes())
        name_length, extra_length = struct.unpack_from('<HH', data, info.header_offset + 26)
        offset = info.header_offset + 30 + name_length + extra_length
        data[offset] ^= 0x80
        self.archive.write_bytes(data)
        self.restore()
        self.app.messagebox.showerror.assert_called_once()
        self.assertEqual((self.user / 'savedata/fixture.bin').read_bytes(), b'savedata')

    def test_failed_second_replacement_rolls_back_both_folders(self):
        self.app._write_save_archive(self.archive)
        for name in ('savedata', 'trophy'):
            (self.user / name / 'fixture.bin').write_bytes(b'keep current progress')
        replace = os.replace

        def fail_second(source, target):
            source = Path(source)
            if source.name == 'trophy' and source.parent.name.startswith('.uncharted-save-restore-'):
                raise OSError('injected restore failure')
            return replace(source, target)

        with patch.object(launcher.os, 'replace', side_effect=fail_second):
            self.restore()
        self.app.messagebox.showerror.assert_called_once()
        for name in ('savedata', 'trophy'):
            self.assertEqual((self.user / name / 'fixture.bin').read_bytes(), b'keep current progress')

    def test_export_inside_savedata_is_rejected(self):
        with self.assertRaises(ValueError):
            self.app._write_save_archive(self.user / 'savedata/backup.zip')
        self.assertFalse((self.user / 'savedata/backup.zip').exists())

    def test_running_game_blocks_export_and_restore(self):
        self.app.process = object()
        self.app.export_saves()
        self.app.import_saves()
        self.app.filedialog.asksaveasfilename.assert_not_called()
        self.app.filedialog.askopenfilename.assert_not_called()


if __name__ == '__main__':
    unittest.main()
