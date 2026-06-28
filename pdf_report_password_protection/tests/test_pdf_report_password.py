# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter

class TestPdfReportPasswordProtection(TransactionCase):

    def setUp(self):
        super(TestPdfReportPasswordProtection, self).setUp()
        self.report_model = self.env['ir.actions.report']
        
        # Create a blank PDF content for testing
        writer = PdfFileWriter()
        writer.addBlankPage(width=200, height=200)
        buffer = BytesIO()
        writer.write(buffer)
        self.blank_pdf_content = buffer.getvalue()
        
        # Create a report action record with password enabled
        self.report_action = self.report_model.create({
            'name': 'Test Protected Report',
            'model': 'res.partner',
            'report_name': 'test_protected_report',
            'report_type': 'qweb-pdf',
            'is_password': True,
            'password_name': 'secure_password_123',
        })

    def test_01_apply_password_protection_enabled(self):
        """Test if PDF is properly encrypted when is_password is True."""
        # The second argument pwd is computationally ignored by the method in favor of self.password_name
        encrypted_pdf = self.report_action.apply_password_protection(self.blank_pdf_content, 'ignored_pwd')
        
        # Verify it's encrypted
        reader = PdfFileReader(BytesIO(encrypted_pdf))
        self.assertTrue(reader.isEncrypted, "The PDF should be encrypted when is_password is True.")
        
        # Verify password is correct
        # PyPDF2 decrypt returns True/False or 1/2/0 depending on version and success
        decrypt_success = reader.decrypt('secure_password_123')
        self.assertTrue(decrypt_success, "The PDF should be decryptable with the correct password.")
        
        # Verify wrong password fails
        reader2 = PdfFileReader(BytesIO(encrypted_pdf))
        decrypt_wrong = reader2.decrypt('wrong_password')
        self.assertFalse(decrypt_wrong, "The PDF should not be decryptable with an incorrect password.")

    def test_02_apply_password_protection_disabled(self):
        """Test if PDF remains unencrypted when is_password is False."""
        self.report_action.is_password = False
        unencrypted_pdf = self.report_action.apply_password_protection(self.blank_pdf_content, 'ignored_pwd')
        
        # Verify it's not encrypted
        reader = PdfFileReader(BytesIO(unencrypted_pdf))
        self.assertFalse(reader.isEncrypted, "The PDF should not be encrypted when is_password is False.")
