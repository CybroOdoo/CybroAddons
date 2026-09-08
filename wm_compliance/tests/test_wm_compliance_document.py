# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
import logging

from odoo import fields
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmComplianceDocument(TransactionCase):
    """Unit tests verifying document vault expiry tracking and renewal alerts."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmComplianceDocument, self).setUp()

        self.facility = self.env['wm.disposal.facility'].create({
            'name': 'East Coast Facility',
            'facility_type': 'treatment',
        })

        # Create an attachment to satisfy the required attachment_id field
        self.attachment = self.env['ir.attachment'].create({
            'name': 'test_doc.pdf',
            'type': 'binary',
            'raw': b'PDF content data',
        })

    def test_document_expiry_reminders(self):
        """
        Test that document expiry reminders behaves as expected.
        """
        today = fields.Date.today()

        # Odoo 19: Get default activity type
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_activity_type:
            todo_activity_type = self.env['mail.activity.type'].search([('category', '=', 'default')], limit=1)

        # 1. Create document expiring in 31 days (reminder_days = 30)
        # reminder_date = expiry_date - 30 = today + 1 (should NOT trigger today)
        doc_future = self.env['wm.compliance.document'].create({
            'name': 'Future Permit',

            'document_type': 'permit',
            'expiry_date': today + datetime.timedelta(days=31),
            'reminder_days': 30,
            'attachment_id': self.attachment.id,
        })

        # 2. Create document expiring in 29 days (reminder_days = 30)
        # reminder_date = expiry_date - 30 = today - 1 (SHOULD trigger today)
        doc_expiring = self.env['wm.compliance.document'].create({
            'name': 'Expiring Permit',

            'document_type': 'licence',
            'expiry_date': today + datetime.timedelta(days=29),
            'reminder_days': 30,
            'attachment_id': self.attachment.id,
        })

        # Clear any existing activities to ensure isolated test state
        self.env['mail.activity'].search([
            ('res_model', '=', 'wm.compliance.document')
        ]).unlink()

        # Run document expiry cron
        self.env['wm.compliance.document'].cron_check_document_expiry()

        # Check doc_future reminder (should not exist)
        activity_future = self.env['mail.activity'].search([
            ('res_model', '=', 'wm.compliance.document'),
            ('res_id', '=', doc_future.id),
        ])
        self.assertEqual(len(activity_future), 0)

        # Check doc_expiring reminder (should exist)
        activity_expiring = self.env['mail.activity'].search([
            ('res_model', '=', 'wm.compliance.document'),
            ('res_id', '=', doc_expiring.id),
        ])
        self.assertEqual(len(activity_expiring), 1)
        self.assertIn("Expiring Permit", activity_expiring.summary)

        _logger.info('PASS: test_document_expiry_reminders')

    def test_document_attachment_creation(self):
        """
        Test that document attachment creation behaves as expected.
        """
        import base64
        doc = self.env['wm.compliance.document'].create({
            'name': 'Test Upload Permit',
            'document_type': 'permit',
            'expiry_date': fields.Date.today() + datetime.timedelta(days=10),
            'attachment_file': base64.b64encode(b'File content data'),
            'attachment_filename': 'uploaded_permit.pdf',
        })
        self.assertTrue(doc.attachment_id)
        self.assertEqual(doc.attachment_id.name, 'uploaded_permit.pdf')
        # datas field returns base64 bytes, let's decode to assert matching content
        self.assertEqual(base64.b64decode(doc.attachment_id.datas), b'File content data')
        _logger.info('PASS: test_document_attachment_creation')
