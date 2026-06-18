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
from odoo.tests.common import TransactionCase, tagged
from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader


@tagged('at_install', 'post_install', 'pdf_report_password_protection')
class TestIrActionsReport(TransactionCase):
    """Test suite for PDF report password protection model"""

    def setUp(self):
        super(TestIrActionsReport, self).setUp()
        self.report = self.env['ir.actions.report'].create({
            'name': 'Test Report',
            'model': 'res.users',
            'report_name': 'test.report',
            'report_type': 'qweb-pdf',
            'is_password': True,
            'password_name': 'secret123'
        })
        # Create a simple dummy PDF content
        output = PdfFileWriter()
        output.addBlankPage(612, 792)
        buf = BytesIO()
        output.write(buf)
        self.dummy_pdf_content = buf.getvalue()

    def test_apply_password_protection(self):
        """Verify that PDF is encrypted when password protection is enabled"""
        protected_pdf = self.report.apply_password_protection(self.dummy_pdf_content, self.report.password_name)
        
        # Verify it's still a PDF
        self.assertTrue(protected_pdf.startswith(b'%PDF'), "Result should be a PDF file")
        
        # Verify it's encrypted
        reader = PdfFileReader(BytesIO(protected_pdf))
        self.assertTrue(reader.isEncrypted, "PDF should be encrypted")
        
        # Verify it can be decrypted with the password
        self.assertTrue(reader.decrypt('secret123'), "Should be able to decrypt with the set password")

    def test_no_password_protection(self):
        """Verify that PDF is NOT encrypted when protection is disabled"""
        self.report.is_password = False
        unprotected_pdf = self.report.apply_password_protection(self.dummy_pdf_content, self.report.password_name)
        
        reader = PdfFileReader(BytesIO(unprotected_pdf))
        self.assertFalse(reader.isEncrypted, "PDF should NOT be encrypted when is_password is False")
