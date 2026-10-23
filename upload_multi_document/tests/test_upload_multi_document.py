#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestUploadMultiDocument(TransactionCase):
    """Test suite for Upload Multiple Documents functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({'name': 'Customer 1'})
        cls.partner_2 = cls.env['res.partner'].create({'name': 'Customer 2'})
        cls.upload_model = cls.env['upload.multi.documents']
        cls.sample_b64 = base64.b64encode(b"Dummy file content").decode('utf-8')

    def _attachments(self, partner, name):
        return self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', partner.id),
            ('name', '=', name),
        ])

    def test_document_file_create_raw_base64(self):
        """Test document_file_create with raw base64 data for multiple records."""
        res = self.upload_model.document_file_create(
            value=self.sample_b64,
            name="test_document.txt",
            selected_ids=[self.partner_1.id, self.partner_2.id],
            model="res.partner",
        )
        self.assertTrue(res)
        attachments_p1 = self._attachments(self.partner_1, 'test_document.txt')
        attachments_p2 = self._attachments(self.partner_2, 'test_document.txt')
        self.assertEqual(len(attachments_p1), 1)
        self.assertEqual(len(attachments_p2), 1)
        self.assertEqual(bytes(attachments_p1.raw), b"Dummy file content")

    def test_document_file_create_data_uri_scheme(self):
        """Test document_file_create when file data contains a data URI prefix."""
        res = self.upload_model.document_file_create(
            value=f"data:text/plain;base64,{self.sample_b64}",
            name="sample_report.pdf",
            selected_ids=[self.partner_1.id],
            model="res.partner",
        )
        self.assertTrue(res)
        attachment = self._attachments(self.partner_1, 'sample_report.pdf')
        self.assertEqual(len(attachment), 1)
        self.assertEqual(bytes(attachment.raw), b"Dummy file content")

    def test_document_file_create_invalid_base64(self):
        """Invalid base64 data raises a UserError and creates nothing."""
        with self.assertRaises(UserError):
            self.upload_model.document_file_create(
                value="not*valid*base64!",
                name="bad.png",
                selected_ids=[self.partner_1.id],
                model="res.partner",
            )
        self.assertFalse(self._attachments(self.partner_1, 'bad.png'))

    def test_document_file_create_empty_selection(self):
        """Test document_file_create with empty selected_ids."""
        res = self.upload_model.document_file_create(
            value=self.sample_b64,
            name="empty_test.txt",
            selected_ids=[],
            model="res.partner",
        )
        self.assertFalse(res)

    def test_document_file_create_empty_value(self):
        """Empty/False values are rejected instead of creating empty attachments."""
        for value in (False, None, "", "data:text/plain;base64,"):
            with self.subTest(value=value), self.assertRaises(UserError):
                self.upload_model.document_file_create(
                    value=value,
                    name="false_val.txt",
                    selected_ids=[self.partner_1.id],
                    model="res.partner",
                )
        self.assertFalse(self._attachments(self.partner_1, 'false_val.txt'))

    def test_document_file_create_invalid_target(self):
        """Unknown models, non-integer ids and missing records are rejected."""
        with self.assertRaises(UserError):
            self.upload_model.document_file_create(
                self.sample_b64, "a.txt", [self.partner_1.id], "no.such.model")
        with self.assertRaises(UserError):
            self.upload_model.document_file_create(
                self.sample_b64, "a.txt", ["1; DROP"], "res.partner")
        with self.assertRaises(UserError):
            self.upload_model.document_file_create(
                self.sample_b64, "a.txt", [self.partner_1.id, 999999999], "res.partner")

    def test_document_file_create_access_rights(self):
        """A user without write access on the targets gets an AccessError."""
        user = new_test_user(self.env, login='umd_portal_user', groups='base.group_portal')
        model = self.upload_model.with_user(user)
        with self.assertRaises(AccessError):
            model.document_file_create(
                self.sample_b64, "denied.txt", [self.partner_1.id], "res.partner")
        self.assertFalse(self._attachments(self.partner_1, 'denied.txt'))
