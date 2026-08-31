# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import ValidationError
import base64


class TestPdfSignature(common.TransactionCase):
    """ Test suite for Reports With Signature """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create a Job
        cls.job = cls.env['hr.job'].create({
            'name': 'CEO'
        })
        
        # Create a User
        cls.user_signer = cls.env['res.users'].create({
            'name': 'Test Signer',
            'login': 'test_signer',
            'email': 'signer@example.com',
        })
        
        # Create an Employee linked to the User and Job
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Signer',
            'user_id': cls.user_signer.id,
            'job_id': cls.job.id,
        })
        
        # Company
        cls.company = cls.env.user.company_id
        
        cls.webp_data = base64.b64encode(b'RIFF\x00\x00\x00\x00WEBPVP8 ').decode('utf-8')
        cls.png_data = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR').decode('utf-8')

    def test_01_compute_job_id(self):
        """ Test job_id is computed correctly based on signed_user_id """
        # Set user as signer
        self.company.signed_user_id = self.user_signer.id
        self.assertEqual(self.company.job_id.id, self.job.id, "Job ID should be correctly computed from the related employee.")
        
        # Clear user
        self.company.signed_user_id = False
        self.assertFalse(self.company.job_id, "Job ID should be empty when no user is selected.")

    def test_02_signature_file_type_validation_webp(self):
        """ Test ValidationError is raised when signature is WEBP format """
        with self.assertRaises(ValidationError) as e:
            self.company.signature = self.webp_data
        
        self.assertIn("WEBP file format is not supported", str(e.exception))

    def test_03_signature_file_type_validation_valid(self):
        """ Test valid file format does not raise ValidationError """
        self.company.signature = self.png_data
        self.assertTrue(self.company.signature)

    def test_04_base_document_layout_related_fields(self):
        """ Test related fields on base.document.layout """
        self.company.write({
            'signed_user_id': self.user_signer.id,
            'signature': self.png_data,
        })
        
        # Create document layout
        layout = self.env['base.document.layout'].create({
            'company_id': self.company.id,
        })
        
        self.assertEqual(layout.signature, self.png_data, "Signature should match company signature.")
        self.assertEqual(layout.signed_user_id.id, self.user_signer.id, "Signed User should match company signed user.")
        self.assertEqual(layout.job_id.id, self.job.id, "Job ID should match company job ID.")
        self.assertTrue(layout.signed_time, "Signed time should be populated.")
