# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import base64
from unittest.mock import MagicMock, patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test cases for res.partner functions defined in
    import_partner_image_from_url/models/res_partner.py"""

    # Minimal 1x1 PNG encoded as base64 (valid image bytes)
    FAKE_IMAGE_B64 = (
        b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4'
        b'2mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    )
    FAKE_IMAGE_BYTES = base64.b64decode(FAKE_IMAGE_B64)

    def _mock_response(self, status_code=200, content=None, content_type='image/png'):
        """Build a fake requests.Response object."""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.content = content or self.FAKE_IMAGE_BYTES
        mock_resp.headers = {'Content-Type': content_type}
        return mock_resp

    # -----------------------------------------------------------------
    # Tests for _download_image_from_url
    # -----------------------------------------------------------------

    def test_download_image_from_url_success(self):
        """_download_image_from_url should return base64-encoded image bytes
        when the HTTP response is 200 and Content-Type is an image type."""
        partner = self.env['res.partner'].create({'name': 'Test Partner DL'})
        with patch('requests.get', return_value=self._mock_response()) as mock_get:
            result = partner._download_image_from_url('https://example.com/img.png')
            mock_get.assert_called_once_with('https://example.com/img.png', timeout=10)
        self.assertEqual(result, base64.b64encode(self.FAKE_IMAGE_BYTES))

    def test_download_image_from_url_non_200_raises_user_error(self):
        """_download_image_from_url must raise UserError when status != 200."""
        partner = self.env['res.partner'].create({'name': 'Test Partner 404'})
        with patch('requests.get', return_value=self._mock_response(status_code=404)):
            with self.assertRaises(UserError):
                partner._download_image_from_url('https://example.com/missing.png')

    def test_download_image_from_url_non_image_content_type_raises_user_error(self):
        """_download_image_from_url must raise UserError when Content-Type is
        not an image (e.g. text/html)."""
        partner = self.env['res.partner'].create({'name': 'Test Partner HTML'})
        with patch('requests.get',
                   return_value=self._mock_response(content_type='text/html')):
            with self.assertRaises(UserError):
                partner._download_image_from_url('https://example.com/page.html')

    def test_download_image_from_url_request_exception_raises_user_error(self):
        """_download_image_from_url must raise UserError when requests raises
        a network-level exception."""
        import requests
        partner = self.env['res.partner'].create({'name': 'Test Partner Net'})
        with patch('requests.get',
                   side_effect=requests.exceptions.ConnectionError('timeout')):
            with self.assertRaises(UserError):
                partner._download_image_from_url('https://example.com/img.png')

    # -----------------------------------------------------------------
    # Tests for _onchange_partner_image_url
    # -----------------------------------------------------------------

    def test_onchange_partner_image_url_valid_url_sets_image(self):
        """_onchange_partner_image_url must download and set image_1920 when the
        URL starts with https:// and download succeeds."""
        partner = self.env['res.partner'].new({'name': 'Onchange Partner'})
        partner.partner_image_url = 'https://example.com/photo.png'
        with patch.object(
            type(partner), '_download_image_from_url',
            return_value=self.FAKE_IMAGE_B64
        ):
            partner._onchange_partner_image_url()
        self.assertEqual(partner.image_1920, self.FAKE_IMAGE_B64)

    def test_onchange_partner_image_url_failed_download_clears_image(self):
        """_onchange_partner_image_url must set image_1920 to False when the
        download raises an exception."""
        partner = self.env['res.partner'].new({'name': 'Onchange Fail Partner'})
        partner.partner_image_url = 'https://bad-url.example.com/x.png'
        with patch.object(
            type(partner), '_download_image_from_url',
            side_effect=Exception('network error')
        ):
            partner._onchange_partner_image_url()
        self.assertFalse(partner.image_1920)

    def test_onchange_partner_image_url_no_url_does_nothing(self):
        """_onchange_partner_image_url must not attempt any download when
        partner_image_url is falsy."""
        partner = self.env['res.partner'].new({'name': 'Onchange Empty Partner'})
        partner.partner_image_url = False
        with patch('requests.get') as mock_get:
            partner._onchange_partner_image_url()
            mock_get.assert_not_called()

    def test_onchange_partner_image_url_non_http_url_does_nothing(self):
        """_onchange_partner_image_url must not call _download_image_from_url
        when the URL does not start with http:// or https://."""
        partner = self.env['res.partner'].new({'name': 'Onchange FTP Partner'})
        partner.partner_image_url = 'ftp://files.example.com/img.png'
        with patch('requests.get') as mock_get:
            partner._onchange_partner_image_url()
            mock_get.assert_not_called()

    # -----------------------------------------------------------------
    # Tests for create (overridden via @api.model_create_multi)
    # -----------------------------------------------------------------

    def test_create_with_image_url_sets_image(self):
        """Creating a partner with a partner_image_url must trigger image
        download and store the result in image_1920."""
        with patch('requests.get', return_value=self._mock_response()):
            partner = self.env['res.partner'].create({
                'name': 'Created With URL',
                'partner_image_url': 'https://example.com/avatar.png',
            })
        self.assertTrue(partner.image_1920,
                        "image_1920 should be set after create with valid URL.")

    def test_create_without_image_url_does_not_set_image(self):
        """Creating a partner without a partner_image_url must not set image_1920
        via the download path (image_1920 stays at its default)."""
        with patch('requests.get') as mock_get:
            partner = self.env['res.partner'].create({'name': 'No URL Partner'})
            mock_get.assert_not_called()
        # image_1920 default is False/empty when not explicitly provided
        self.assertFalse(partner.image_1920)

    def test_create_with_failing_url_silently_skips_image(self):
        """When image download fails during create, UserError is silently caught
        and the record is still created without image_1920."""
        with patch('requests.get', return_value=self._mock_response(status_code=500)):
            partner = self.env['res.partner'].create({
                'name': 'Failed URL Partner',
                'partner_image_url': 'https://example.com/broken.png',
            })
        self.assertTrue(partner.exists(), "Partner record should still be created.")
        self.assertFalse(partner.image_1920,
                         "image_1920 should remain unset when download fails on create.")

    # -----------------------------------------------------------------
    # Tests for write (overridden)
    # -----------------------------------------------------------------

    def test_write_with_image_url_updates_image(self):
        """Writing a new partner_image_url on an existing partner must
        trigger image download and update image_1920."""
        partner = self.env['res.partner'].create({'name': 'Write URL Partner'})
        with patch('requests.get', return_value=self._mock_response()):
            partner.write({'partner_image_url': 'https://example.com/new.png'})
        self.assertTrue(partner.image_1920,
                        "image_1920 should be updated after write with valid URL.")

    def test_write_clearing_image_url_clears_image(self):
        """Writing partner_image_url=False on a partner must clear image_1920."""
        partner = self.env['res.partner'].create({'name': 'Clear URL Partner'})
        # First set an image manually
        partner.image_1920 = self.FAKE_IMAGE_B64
        # Now clear the URL
        with patch('requests.get') as mock_get:
            partner.write({'partner_image_url': False})
            mock_get.assert_not_called()
        self.assertFalse(partner.image_1920,
                         "image_1920 should be cleared when partner_image_url is set to False.")

    def test_write_unrelated_field_does_not_trigger_download(self):
        """Writing a field unrelated to partner_image_url must not call
        _download_image_from_url at all."""
        partner = self.env['res.partner'].create({'name': 'Unrelated Write Partner'})
        with patch('requests.get') as mock_get:
            partner.write({'phone': '+91 9999999999'})
            mock_get.assert_not_called()
