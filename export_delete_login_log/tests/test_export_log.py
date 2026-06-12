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
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestExportLog(TransactionCase):
    """Test cases for ExportLog model (export.log)"""

    def setUp(self):
        super().setUp()
        # Get the ir.model record for res.partner (a common model)
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)
        # Create a sample partner record to reference
        self.partner = self.env['res.partner'].create({'name': 'Test Export Partner'})
        # Get some ir.model.fields to link as exported fields
        self.partner_name_field = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', self.partner_model.id),
            ('name', '=', 'name'),
        ], limit=1)
        self.partner_email_field = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', self.partner_model.id),
            ('name', '=', 'email'),
        ], limit=1)

    def test_export_log_creation(self):
        """Test that an export.log record can be created with all required fields."""
        export_log = self.env['export.log'].sudo().create({
            'rec_model': self.partner_model.id,
            'rec_id': str(self.partner.id),
            'rec_name': self.partner.name,
            'exported_fields_ids': [
                (4, self.partner_name_field.id),
            ],
            'export_user_id': self.env.user.id,
        })
        self.assertTrue(export_log.exists(), "ExportLog record should exist after creation.")
        self.assertEqual(export_log.rec_model.id, self.partner_model.id)
        self.assertEqual(export_log.rec_id, str(self.partner.id))
        self.assertEqual(export_log.rec_name, 'Test Export Partner')

    def test_export_log_default_export_date(self):
        """Test that export_date is automatically set on creation."""
        export_log = self.env['export.log'].sudo().create({
            'rec_model': self.partner_model.id,
            'rec_id': str(self.partner.id),
            'rec_name': self.partner.name,
        })
        self.assertIsNotNone(export_log.export_date,
                             "export_date should have a default value set automatically.")

    def test_export_log_default_export_user(self):
        """Test that export_user_id defaults to the current user."""
        export_log = self.env['export.log'].sudo().create({
            'rec_model': self.partner_model.id,
            'rec_id': str(self.partner.id),
            'rec_name': self.partner.name,
        })
        self.assertEqual(export_log.export_user_id.id, self.env.user.id,
                         "Default export_user_id should be the current user.")

    def test_export_log_multiple_exported_fields(self):
        """Test that multiple fields can be linked as exported fields."""
        fields_to_export = [self.partner_name_field.id,
                            self.partner_email_field.id]
        export_log = self.env['export.log'].sudo().create({
            'rec_model': self.partner_model.id,
            'rec_id': str(self.partner.id),
            'rec_name': self.partner.name,
            'exported_fields_ids': [(6, 0, fields_to_export)],
        })
        self.assertEqual(
            len(export_log.exported_fields_ids), 2,
            "ExportLog should store all exported fields linked to it."
        )

    def test_action_create_export_log(self):
        """Test the action_create_export_log method creates records correctly."""
        vals = {
            'records': [
                {
                    'rec_model': 'res.partner',
                    'rec_id': self.partner.id,
                }
            ],
            'exportList': [
                {'field_name': 'name'},
            ],
        }
        before_count = self.env['export.log'].sudo().search_count([])
        self.env['export.log'].sudo().action_create_export_log(vals)
        after_count = self.env['export.log'].sudo().search_count([])
        self.assertEqual(
            after_count, before_count + 1,
            "action_create_export_log should create one new export.log record."
        )

    def test_action_create_export_log_correct_model(self):
        """Test that action_create_export_log stores the correct model."""
        vals = {
            'records': [
                {
                    'rec_model': 'res.partner',
                    'rec_id': self.partner.id,
                }
            ],
            'exportList': [
                {'field_name': 'name'},
            ],
        }
        self.env['export.log'].sudo().action_create_export_log(vals)
        latest_log = self.env['export.log'].sudo().search(
            [], order='id desc', limit=1)
        self.assertEqual(
            latest_log.rec_model.model, 'res.partner',
            "Newly created export.log should reference the correct model."
        )

    def test_action_create_export_log_rec_id(self):
        """Test that action_create_export_log stores the correct record ID."""
        vals = {
            'records': [
                {
                    'rec_model': 'res.partner',
                    'rec_id': self.partner.id,
                }
            ],
            'exportList': [
                {'field_name': 'name'},
            ],
        }
        self.env['export.log'].sudo().action_create_export_log(vals)
        latest_log = self.env['export.log'].sudo().search(
            [], order='id desc', limit=1)
        self.assertEqual(
            str(latest_log.rec_id), str(self.partner.id),
            "Newly created export.log should store the exported record's ID."
        )

    def test_export_log_rec_name(self):
        """Test that action_create_export_log stores the correct record name."""
        vals = {
            'records': [
                {
                    'rec_model': 'res.partner',
                    'rec_id': self.partner.id,
                }
            ],
            'exportList': [
                {'field_name': 'name'},
            ],
        }
        self.env['export.log'].sudo().action_create_export_log(vals)
        latest_log = self.env['export.log'].sudo().search(
            [], order='id desc', limit=1)
        self.assertIn(
            'Test Export Partner', latest_log.rec_name,
            "Newly created export.log rec_name should match the partner name."
        )

    def test_export_log_description(self):
        """Test the model description is correctly set."""
        self.assertEqual(
            self.env['export.log']._description, 'Export Log',
            "ExportLog model description should be 'Export Log'."
        )

    def test_export_log_no_model(self):
        """Test that export.log can be created without specifying a model."""
        export_log = self.env['export.log'].sudo().create({
            'rec_id': '999',
            'rec_name': 'Orphan Record',
        })
        self.assertTrue(export_log.exists())
        self.assertFalse(export_log.rec_model,
                         "rec_model should be False if not provided.")
