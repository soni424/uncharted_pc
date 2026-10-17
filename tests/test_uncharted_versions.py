import io
import json
import sys
import unittest
from unittest.mock import patch

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher


class ForkVersionTests(unittest.TestCase):
    def test_fork_revision_and_upstream_updates_sort_in_order(self):
        for older, newer in (('0.3.3.8', '0.3.3.9'), ('0.3.3.9', '0.3.3.10'),
                             ('0.3.3.99', '0.3.4.1'), ('0.3.4.99', '0.4.0.1')):
            with self.subTest(older=older, newer=newer):
                self.assertLess(launcher.version_tuple(older), launcher.version_tuple(newer))

    def test_updates_use_fork_release_and_preserve_four_components(self):
        url = 'https://github.com/soni424/uncharted_pc/releases/download/v0.3.3.9/uncharted-windows-v0.3.3.9.zip'
        payload = {'tag_name': 'v0.3.3.9', 'assets': [
            {'name': 'uncharted-windows-v0.3.3.9.zip.sha256', 'browser_download_url': url + '.sha256'},
            {'name': 'uncharted-windows-v0.3.3.9.zip', 'browser_download_url': url}]}
        with patch.object(launcher.urllib.request, 'urlopen',
                          return_value=io.BytesIO(json.dumps(payload).encode())) as request:
            self.assertEqual(launcher.latest_release(), ('0.3.3.9', url, launcher.RELEASES_PAGE))
        self.assertEqual(request.call_args.args[0].full_url,
                         'https://api.github.com/repos/soni424/uncharted_pc/releases/latest')


if __name__ == '__main__':
    unittest.main()
