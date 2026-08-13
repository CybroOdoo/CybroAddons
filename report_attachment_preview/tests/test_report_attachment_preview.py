# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali V P (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestReportAttachmentPreview(HttpCase):
    """Test case for the report_attachment_preview module."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        # Create a test user for authentication
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_preview',
            'password': 'test_password',
        })
        
        # Create a dummy attachment for testing
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'test_preview.pdf',
            'type': 'binary',
            'datas': b'JVBERi0xLjQK',  # Dummy PDF base64 data
            'mimetype': 'application/pdf',
            'public': True,
        })

    def test_content_common_inline_disposition(self):
        """Test if the Content-Disposition header is set to inline for
        binary content."""
        self.authenticate('test_user_preview', 'test_password')
        # Request the attachment via /web/content
        url = f'/web/content/{self.attachment.id}'
        response = self.url_open(url)

        # Check that the request was successful
        self.assertEqual(
            response.status_code, 200,
            "Failed to fetch the attachment content"
        )

        # Verify the Content-Disposition header contains 'inline'
        content_disposition = response.headers.get('Content-Disposition', '')
        self.assertIn(
            'inline', content_disposition,
            "The Content-Disposition header should contain 'inline'"
        )
