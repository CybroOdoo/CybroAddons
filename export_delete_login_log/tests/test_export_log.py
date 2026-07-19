# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase


class TestExportLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestExportLog, cls).setUpClass()

        # 1. Fetch metadata required for assertions
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        # Get specific fields from ir.model.fields to verify relation matching
        cls.field_name = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'name')
        ], limit=1)
        cls.field_email = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'email')
        ], limit=1)

        # 2. Create sample test records to mock an export target
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Export Test Partner A',
            'email': 'partner_a@test.com'
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Export Test Partner B',
            'email': 'partner_b@test.com'
        })

    def test_01_create_export_log_success(self):
        """Test that single record export logging creates a accurate export.log record."""

        # Construct the exact data structure expected by action_create_export_log
        vals = {
            'records': [
                {
                    'rec_model': 'res.partner',
                    'rec_id': self.partner_1.id
                }
            ],
            'exportList': [
                {'field_name': 'name'},
                {'field_name': 'email'}
            ]
        }

        # Call the method
        self.env['export.log'].action_create_export_log(vals)

        # Search for the created log
        log = self.env['export.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', '=', str(self.partner_1.id))
        ])

        # Assertions
        self.assertTrue(log, "Export log was not created.")
        self.assertEqual(log.rec_name, self.partner_1.name, "The logged record name does not match.")
        self.assertEqual(log.export_user_id, self.env.user, "The active environment user was not logged.")

        # Verify Many2many field commands linked the correct ir.model.fields records
        expected_fields = self.field_name + self.field_email
        self.assertEqual(log.exported_fields_ids, expected_fields,
                         "The logged fields do not match the expected fields.")

    def test_02_create_export_log_multiple_records(self):
        """Test that multiple records passed to the vals dict create separate logs simultaneously."""

        vals = {
            'records': [
                {'rec_model': 'res.partner', 'rec_id': self.partner_1.id},
                {'rec_model': 'res.partner', 'rec_id': self.partner_2.id}
            ],
            'exportList': [
                {'field_name': 'name'}
            ]
        }

        # Execute
        self.env['export.log'].action_create_export_log(vals)

        # Check log for Partner 1
        log_1 = self.env['export.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', '=', str(self.partner_1.id))
        ])
        # Check log for Partner 2
        log_2 = self.env['export.log'].search([
            ('rec_model_id', '=', self.partner_model.id),
            ('rec_id', '=', str(self.partner_2.id))
        ])

        self.assertTrue(log_1, "Export log for record 1 was not created.")
        self.assertTrue(log_2, "Export log for record 2 was not created.")
        self.assertIn(self.field_name, log_1.exported_fields_ids, "Field mapping failed for log 1.")
        self.assertIn(self.field_name, log_2.exported_fields_ids, "Field mapping failed for log 2.")