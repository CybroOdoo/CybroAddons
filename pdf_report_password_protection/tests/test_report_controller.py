# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nandakishore M (odoo@cybrosys.com)
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
from odoo.tests.common import HttpCase, tagged
from PyPDF2 import PdfFileReader, PdfFileWriter
from unittest.mock import patch
from io import BytesIO


@tagged('post_install', '-at_install', 'pdf_report_password_protection')
class TestReportController(HttpCase):
    """Test suite for PDF report password protection controller"""

    def setUp(self):
        super(TestReportController, self).setUp()
        # Create a dedicated test user
        self.user_login = 'report_test_user'
        self.user_password = 'report_test_password'
        self.test_user = self.env['res.users'].create({
            'name': 'Report Test User',
            'login': self.user_login,
            'password': self.user_password,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        # Use an existing system report that is known to work
        self.report = self.env.ref('base.report_ir_model_overview')
        self.report.write({
            'is_password': True,
            'password_name': 'web_secret'
        })
        self.docids = self.env['ir.model'].search([], limit=1).id
        self.report_url = f'/report/pdf/{self.report.report_name}/{self.docids}'

    def test_report_pdf_encrypted(self):
        """Verify that downloading a PDF report via controller returns encrypted content"""
        self.authenticate(self.user_login, self.user_password)
        
        # Generate a valid dummy PDF
        out = PdfFileWriter()
        out.addBlankPage(612, 792)
        buf = BytesIO()
        out.write(buf)
        dummy_pdf = buf.getvalue()
        
        with patch('odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf', 
                   return_value=(dummy_pdf, 'pdf')):
            response = self.url_open(self.report_url)
            
        self.assertEqual(response.status_code, 200, f"Report request failed with {response.status_code}")
        self.assertEqual(response.headers.get('Content-Type'), 'application/pdf')
        
        # Verify encryption
        reader = PdfFileReader(BytesIO(response.content))
        self.assertTrue(reader.isEncrypted, "PDF should be encrypted")
        self.assertTrue(reader.decrypt('web_secret'), "Should be able to decrypt with the set password")

    def test_report_pdf_unencrypted(self):
        """Verify that PDF is not encrypted when is_password is False"""
        self.authenticate(self.user_login, self.user_password)
        self.report.is_password = False
        
        # Generate a valid dummy PDF
        out = PdfFileWriter()
        out.addBlankPage(612, 792)
        buf = BytesIO()
        out.write(buf)
        dummy_pdf = buf.getvalue()
        
        with patch('odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf', 
                   return_value=(dummy_pdf, 'pdf')):
            response = self.url_open(self.report_url)
            
        self.assertEqual(response.status_code, 200)
        reader = PdfFileReader(BytesIO(response.content))
        self.assertFalse(reader.isEncrypted, "PDF should NOT be encrypted")
