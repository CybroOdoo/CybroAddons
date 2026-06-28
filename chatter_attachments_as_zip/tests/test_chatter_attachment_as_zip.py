# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ismail C A (odoo@cybrosys.com)
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
import io
import zipfile
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestChatterAttachmentAsZip(HttpCase):
    """Test cases for the chatter attachments ZIP download controller."""

    def setUp(self):
        super(TestChatterAttachmentAsZip, self).setUp()
        # Create a test partner to link attachments to
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner for Zip Download',
        })
        # Create some test binary content
        self.file1_content = b"This is the content of the first file."
        self.file2_content = b"This is the content of the second file."

        # Create a dedicated test user to run the tests with a known password
        self.test_user = self.env['res.users'].create({
            'name': 'Test Zip User',
            'login': 'test_zip_user',
            'password': 'test_password',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_download_attachments_success(self):
        """Test successful download of attachments as a single zip file."""
        # Create attachments associated with the partner
        self.env['ir.attachment'].create({
            'name': 'file1.txt',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
            'datas': base64.b64encode(self.file1_content),
        })
        self.env['ir.attachment'].create({
            'name': 'file2.txt',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
            'datas': base64.b64encode(self.file2_content),
        })

        # Authenticate as the dedicated test user
        self.authenticate('test_zip_user', 'test_password')

        # Request the download route
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}'
        response = self.url_open(url)

        # Assertions
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        self.assertEqual(response.headers.get('Content-Type'), 'application/zip', "Content-Type must be application/zip")
        self.assertIn(
            f'attachment; filename=attachments_{self.partner.id}.zip',
            response.headers.get('Content-Disposition', ''),
            "Content-Disposition header should match correct zip file name"
        )

        # Verify the ZIP file content
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, 'r') as zip_file:
            # Check files are inside the ZIP
            namelist = zip_file.namelist()
            self.assertIn('file1.txt', namelist, "file1.txt should be in the ZIP file")
            self.assertIn('file2.txt', namelist, "file2.txt should be in the ZIP file")

            # Check contents
            self.assertEqual(zip_file.read('file1.txt'), self.file1_content, "Content of file1.txt should match")
            self.assertEqual(zip_file.read('file2.txt'), self.file2_content, "Content of file2.txt should match")

    def test_download_attachments_exclude_account_move(self):
        """Test that attachments associated with 'account.move' are excluded."""
        # Create an attachment with res_model='account.move' linked to the partner ID
        self.env['ir.attachment'].create({
            'name': 'invoice_file.txt',
            'res_model': 'account.move',
            'res_id': self.partner.id,
            'datas': base64.b64encode(self.file1_content),
        })

        # Authenticate as the dedicated test user
        self.authenticate('test_zip_user', 'test_password')

        # Request the download route
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}'
        response = self.url_open(url)

        # Since only account.move attachment exists, attachments search yields empty,
        # and the controller returns None. Check that response is empty / returns no zip.
        self.assertIn(response.status_code, [204, 200], "Status code should indicate success or no content")
        self.assertNotEqual(response.headers.get('Content-Type'), 'application/zip', "Should not return a zip archive")

    def test_download_attachments_no_attachments(self):
        """Test requesting the route for a res_id with no attachments."""
        # Authenticate as the dedicated test user
        self.authenticate('test_zip_user', 'test_password')

        # Request with a partner ID which has no attachments yet
        url = f'/chatter/attachments/download/zip?res_id={self.partner.id}'
        response = self.url_open(url)

        # Should not return a zip archive
        self.assertIn(response.status_code, [204, 200], "Status code should indicate success or no content")
        self.assertNotEqual(response.headers.get('Content-Type'), 'application/zip', "Should not return a zip archive")

    def test_download_attachments_missing_param(self):
        """Test requesting the route without the res_id parameter."""
        # Call route as anonymous public user (not authenticated) so we don't query system attachments
        url = '/chatter/attachments/download/zip'
        response = self.url_open(url)

        # Verify it resolves to a non-zip response
        self.assertIn(response.status_code, [204, 200], "Status code should indicate success or no content")
        self.assertNotEqual(response.headers.get('Content-Type'), 'application/zip', "Should not return a zip archive")
