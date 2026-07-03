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
import csv
import io
from unittest.mock import MagicMock, patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


def _make_csv_binary(rows, fieldnames=('name', 'partner_image_url')):
    """Helper: build a base64-encoded CSV binary from a list of dicts."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return base64.b64encode(buf.getvalue().encode('utf-8'))


@tagged('post_install', '-at_install')
class TestBulkPartnerImageImport(TransactionCase):
    """Test cases for bulk.partner.image.import wizard defined in
    import_partner_image_from_url/wizard/bulk_partner_image_import.py"""

    # A minimal valid PNG image (1×1 pixel)
    FAKE_IMAGE_BYTES = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4'
        b'2mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    )

    def _mock_response(self, status_code=200, content=None):
        """Return a fake requests.Response with configurable status and content."""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.content = content or self.FAKE_IMAGE_BYTES
        return mock_resp

    def _make_wizard(self, csv_rows, fieldnames=('name', 'partner_image_url')):
        """Convenience: create the transient wizard with a pre-built CSV."""
        return self.env['bulk.partner.image.import'].create({
            'file': _make_csv_binary(csv_rows, fieldnames),
            'filename': 'test_import.csv',
        })

    # -----------------------------------------------------------------
    # Tests for action_import_images
    # -----------------------------------------------------------------

    def test_action_import_images_no_file_raises_user_error(self):
        """action_import_images must raise UserError when no file is uploaded.
        We use .new() (in-memory record) to bypass the required=True DB constraint
        so that file can legitimately be False without a DB write."""
        wizard = self.env['bulk.partner.image.import'].new({
            'file': False,
            'filename': '',
        })
        with self.assertRaises(UserError,
                               msg="Should raise UserError when file is missing."):
            wizard.action_import_images()

    def test_action_import_images_invalid_encoding_raises_user_error(self):
        """action_import_images must raise UserError for non-UTF-8 file content."""
        # Encode latin-1 bytes that are not valid UTF-8
        bad_bytes = 'naïve,https://example.com/img.png\n'.encode('latin-1')
        wizard = self.env['bulk.partner.image.import'].create({
            'file': base64.b64encode(bad_bytes),
            'filename': 'bad_encoding.csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_images()

    def test_action_import_images_missing_name_column_records_error(self):
        """action_import_images must raise UserError listing lines with missing
        name or image URL fields."""
        # Row has name but no partner_image_url value
        csv_rows = [{'name': '', 'partner_image_url': 'https://example.com/a.png'}]
        wizard = self._make_wizard(csv_rows)
        with self.assertRaises(UserError) as ctx:
            wizard.action_import_images()
        self.assertIn('Missing name or image URL', str(ctx.exception))

    def test_action_import_images_missing_url_column_records_error(self):
        """action_import_images must raise UserError listing lines with empty URL."""
        csv_rows = [{'name': 'Alice', 'partner_image_url': ''}]
        wizard = self._make_wizard(csv_rows)
        with self.assertRaises(UserError) as ctx:
            wizard.action_import_images()
        self.assertIn('Missing name or image URL', str(ctx.exception))

    def test_action_import_images_duplicate_in_csv_records_error(self):
        """action_import_images must raise UserError mentioning duplicate partner
        name when the same name appears more than once in the CSV."""
        # Create a real partner so the first occurrence is found
        self.env['res.partner'].create({'name': 'DuplicatePartner'})
        csv_rows = [
            {'name': 'DuplicatePartner', 'partner_image_url': 'https://ex.com/a.png'},
            {'name': 'DuplicatePartner', 'partner_image_url': 'https://ex.com/b.png'},
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', return_value=self._mock_response()):
            with self.assertRaises(UserError) as ctx:
                wizard.action_import_images()
        self.assertIn("Duplicate partner", str(ctx.exception))

    def test_action_import_images_partner_not_found_records_error(self):
        """action_import_images must raise UserError mentioning partners that
        do not exist in the database."""
        csv_rows = [
            {'name': 'NonExistentPartner_XYZ', 'partner_image_url': 'https://ex.com/img.png'}
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', return_value=self._mock_response()):
            with self.assertRaises(UserError) as ctx:
                wizard.action_import_images()
        self.assertIn('not found', str(ctx.exception))

    def test_action_import_images_multiple_partners_same_name_records_error(self):
        """action_import_images must raise UserError when the partner name
        matches multiple records (ambiguous)."""
        self.env['res.partner'].create({'name': 'AmbiguousPartner'})
        self.env['res.partner'].create({'name': 'AmbiguousPartner'})
        csv_rows = [
            {'name': 'AmbiguousPartner', 'partner_image_url': 'https://ex.com/img.png'}
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', return_value=self._mock_response()):
            with self.assertRaises(UserError) as ctx:
                wizard.action_import_images()
        self.assertIn('Multiple partners found', str(ctx.exception))

    def test_action_import_images_failed_fetch_records_error(self):
        """action_import_images must raise UserError noting the fetch failure when
        requests returns a non-200 response for a valid partner."""
        partner = self.env['res.partner'].create({'name': 'FetchFailPartner'})
        csv_rows = [
            {'name': partner.name, 'partner_image_url': 'https://ex.com/bad.png'}
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', return_value=self._mock_response(status_code=404)):
            with self.assertRaises(UserError) as ctx:
                wizard.action_import_images()
        self.assertIn('Failed to fetch image', str(ctx.exception))

    def test_action_import_images_network_exception_records_error(self):
        """action_import_images must raise UserError listing a network error when
        requests.get raises an exception for a valid partner."""
        import requests as req_lib
        partner = self.env['res.partner'].create({'name': 'NetErrorPartner'})
        csv_rows = [
            {'name': partner.name, 'partner_image_url': 'https://ex.com/x.png'}
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', side_effect=req_lib.exceptions.ConnectionError('fail')):
            with self.assertRaises(UserError) as ctx:
                wizard.action_import_images()
        self.assertIn('Error fetching image', str(ctx.exception))

    def test_action_import_images_success_sets_partner_image(self):
        """action_import_images must update partner.image_1920 when everything
        succeeds (valid CSV, unique partner, 200 response)."""
        partner = self.env['res.partner'].create({'name': 'SuccessPartner'})
        csv_rows = [
            {'name': partner.name, 'partner_image_url': 'https://ex.com/ok.png'}
        ]
        wizard = self._make_wizard(csv_rows)
        with patch('requests.get', return_value=self._mock_response(status_code=200)):
            wizard.action_import_images()   # must NOT raise
        partner.invalidate_recordset()
        self.assertTrue(partner.image_1920,
                        "image_1920 should be populated after a successful bulk import.")
