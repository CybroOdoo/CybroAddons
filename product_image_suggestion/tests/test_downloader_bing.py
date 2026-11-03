# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from io import BytesIO
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

from PIL import Image

from odoo.tests import tagged
from odoo.tests.common import BaseCase

from ..models import downloader
from ..models.bing import Bing


@tagged('post_install', '-at_install', 'product_image_suggestion')
class TestDownloaderAndBing(BaseCase):
    """Test suite covering Bing image scraper and downloader utilities."""

    def setUp(self):
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.tmp_dir.name)
        buf = BytesIO()
        img = Image.new('RGB', (1, 1), color='red')
        img.save(buf, format='PNG')
        self.png_bytes = buf.getvalue()

    def tearDown(self):
        self.tmp_dir.cleanup()
        super().tearDown()

    # -------------------------------------------------------------------------
    # Bing class tests
    # -------------------------------------------------------------------------

    def test_bing_init(self):
        """Bing.__init__ sets properties and validates integer assertions."""
        bing = Bing(
            query='laptop',
            limit=5,
            output_dir=self.output_path,
            adult='off',
            timeout=30,
            filter='photo',
            verbose=False,
        )
        self.assertEqual(bing.query, 'laptop')
        self.assertEqual(bing.limit, 5)
        self.assertEqual(bing.adult, 'off')
        self.assertEqual(bing.timeout, 30)
        self.assertEqual(bing.filter, 'photo')
        self.assertFalse(bing.verbose)

        # limit assertion
        with self.assertRaises(AssertionError):
            Bing('laptop', '5', self.output_path, 'off', 30)

        # timeout assertion
        with self.assertRaises(AssertionError):
            Bing('laptop', 5, self.output_path, 'off', '30')

    def test_bing_get_filter(self):
        """get_filter() translates shorthand filter values into Bing query
        filters."""
        bing = Bing('test', 1, self.output_path, 'off', 10)
        self.assertEqual(
            bing.get_filter('line'), '+filterui:photo-linedrawing'
        )
        self.assertEqual(
            bing.get_filter('linedrawing'), '+filterui:photo-linedrawing'
        )
        self.assertEqual(
            bing.get_filter('photo'), '+filterui:photo-photo'
        )
        self.assertEqual(
            bing.get_filter('clipart'), '+filterui:photo-clipart'
        )
        self.assertEqual(
            bing.get_filter('gif'), '+filterui:photo-animatedgif'
        )
        self.assertEqual(
            bing.get_filter('animatedgif'), '+filterui:photo-animatedgif'
        )
        self.assertEqual(
            bing.get_filter('transparent'), '+filterui:photo-transparent'
        )
        self.assertEqual(bing.get_filter('unknown'), '')
        self.assertEqual(bing.get_filter(''), '')

    def test_bing_save_image_valid(self):
        """save_image() verifies image with Pillow and writes to disk."""
        bing = Bing('test', 1, self.output_path, 'off', 10)
        file_path = self.output_path.joinpath('test_valid.png')

        mock_resp = MagicMock()
        mock_resp.read.return_value = self.png_bytes

        with patch('urllib.request.urlopen', return_value=mock_resp):
            res = bing.save_image('https://example.com/valid.png', file_path)

        self.assertTrue(res)
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), self.png_bytes)

    def test_bing_save_image_invalid(self):
        """save_image() returns False when image data is unidentifiable."""
        bing = Bing('test', 1, self.output_path, 'off', 10, verbose=True)
        file_path = self.output_path.joinpath('test_invalid.png')

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'corrupted_not_an_image_data'

        with patch('urllib.request.urlopen', return_value=mock_resp):
            res = bing.save_image('https://example.com/invalid.png', file_path)

        self.assertFalse(res)
        self.assertFalse(file_path.exists())

    def test_bing_download_image_extensions(self):
        """download_image() preserves valid image extensions or falls back to
        jpg."""
        bing = Bing('test', 5, self.output_path, 'off', 10, verbose=True)

        with patch.object(bing, 'save_image', return_value=True) as mock_save:
            # Valid extension .png
            res1 = bing.download_image('https://example.com/sample.png')
            self.assertEqual(res1, 'https://example.com/sample.png')
            saved_path1 = mock_save.call_args[0][1]
            self.assertEqual(saved_path1.name, 'Image_1.png')

            # URL with query string and no extension -> fallback jpg
            res2 = bing.download_image('https://example.com/image?id=456')
            self.assertEqual(res2, 'https://example.com/image?id=456')
            saved_path2 = mock_save.call_args[0][1]
            self.assertEqual(saved_path2.name, 'Image_2.jpg')

            # Unsupported extension -> fallback jpg
            res3 = bing.download_image('https://example.com/doc.pdf')
            self.assertEqual(res3, 'https://example.com/doc.pdf')
            saved_path3 = mock_save.call_args[0][1]
            self.assertEqual(saved_path3.name, 'Image_3.jpg')

    def test_bing_download_image_exception_handling(self):
        """download_image() rolls back download_count and removes link from seen
        on error."""
        bing = Bing('test', 5, self.output_path, 'off', 10, verbose=True)
        link = 'https://example.com/error.png'
        bing.seen.add(link)
        initial_count = bing.download_count

        with patch.object(
            bing, 'save_image', side_effect=Exception('IO error')
        ):
            res = bing.download_image(link)

        self.assertIsNone(res)
        self.assertEqual(bing.download_count, initial_count)
        self.assertNotIn(link, bing.seen)

    def test_bing_run_success(self):
        """run() parses HTML for image links and downloads up to limit."""
        bing = Bing('apple', 2, self.output_path, 'off', 10)

        html_page_1 = (
            '<html><body>'
            'murl&quot;:&quot;https://example.com/1.png&quot;'
            'murl&quot;:&quot;https://example.com/2.png&quot;'
            'murl&quot;:&quot;https://example.com/3.png&quot;'
            '</body></html>'
        )

        mock_resp_1 = MagicMock()
        mock_resp_1.read.return_value = html_page_1.encode('utf-8')

        with patch(
            'urllib.request.urlopen', return_value=mock_resp_1
        ), patch.object(
            bing, 'download_image'
        ) as mock_dl:
            # Each download increments download_count to respect limit
            def side_effect_dl(link):
                bing.download_count += 1
            mock_dl.side_effect = side_effect_dl

            seen = bing.run()

        self.assertEqual(len(seen), 2)
        self.assertIn('https://example.com/1.png', seen)
        self.assertIn('https://example.com/2.png', seen)
        self.assertNotIn('https://example.com/3.png', seen)

    def test_bing_run_empty_html_terminates(self):
        """run() terminates while loop when empty HTML is returned."""
        bing = Bing('empty', 2, self.output_path, 'off', 10)

        mock_resp = MagicMock()
        mock_resp.read.return_value = b''

        with patch('urllib.request.urlopen', return_value=mock_resp):
            seen = bing.run()

        self.assertEqual(seen, set())

    # -------------------------------------------------------------------------
    # Downloader module tests
    # -------------------------------------------------------------------------

    def test_downloader_download_success(self):
        """downloader.download() creates directory and runs Bing search."""
        target_dir = self.output_path.joinpath('test_dir')

        with patch.object(
            Bing, 'run', return_value={'https://example.com/result.jpg'}
        ) as mock_run:
            results = downloader.download(
                query='car',
                limit=1,
                output_dir=str(target_dir),
                adult_filter_off=False,
            )

        self.assertEqual(results, {'https://example.com/result.jpg'})
        mock_run.assert_called_once()
        self.assertTrue(target_dir.joinpath('car').is_dir())

    def test_downloader_download_force_replace(self):
        """downloader.download() removes existing directory if force_replace is
        True."""
        image_dir = self.output_path.joinpath('replace_test', 'phone')
        image_dir.mkdir(parents=True, exist_ok=True)
        marker = image_dir.joinpath('old_file.txt')
        marker.write_text('old')
        self.assertTrue(marker.exists())

        with patch.object(Bing, 'run', return_value=set()):
            downloader.download(
                query='phone',
                limit=1,
                output_dir=str(self.output_path.joinpath('replace_test')),
                force_replace=True,
            )

        self.assertFalse(marker.exists())
        self.assertTrue(image_dir.is_dir())

    def test_downloader_download_mkdir_failure(self):
        """downloader.download() logs exception and returns empty set if mkdir
        fails."""
        with patch.object(
            Path, 'mkdir', side_effect=OSError('Permission denied')
        ):
            results = downloader.download(
                query='forbidden',
                limit=1,
                output_dir=str(self.output_path),
            )

        self.assertEqual(results, set())
