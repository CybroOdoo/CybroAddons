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
    """Test cases for ExportLog model (export.log) and
    action_create_export_log method."""

    def setUp(self):
        super().setUp()
        self.ExportLog = self.env['export.log']

        # Resolve the res.partner ir.model record
        self.partner_ir_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)

        # Create a real partner to export
        self.partner = self.env['res.partner'].search(
            [('is_company', '=', True)], limit=1)
        if not self.partner:
            self.partner = self.env['res.partner'].create({
                'name': 'Export Test Company',
                'is_company': True,
            })

        # Pick real field objects from res.partner for exported_fields_ids
        self.field_name = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', self.partner_ir_model.id),
            ('name', '=', 'name'),
        ], limit=1)
        self.field_email = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', self.partner_ir_model.id),
            ('name', '=', 'email'),
        ], limit=1)

    # ------------------------------------------------------------------
    # ExportLog model – field existence
    # ------------------------------------------------------------------

    def test_field_rec_model_id_exists(self):
        """rec_model_id field must be present on export.log."""
        self.assertIn('rec_model_id', self.ExportLog._fields)

    def test_field_rec_id_exists(self):
        """rec_id field must be present on export.log."""
        self.assertIn('rec_id', self.ExportLog._fields)

    def test_field_rec_name_exists(self):
        """rec_name field must be present on export.log."""
        self.assertIn('rec_name', self.ExportLog._fields)

    def test_field_export_date_exists(self):
        """export_date field must be present on export.log."""
        self.assertIn('export_date', self.ExportLog._fields)

    def test_field_exported_fields_ids_exists(self):
        """exported_fields_ids field must be present on export.log."""
        self.assertIn('exported_fields_ids', self.ExportLog._fields)

    def test_field_export_user_id_exists(self):
        """export_user_id field must be present on export.log."""
        self.assertIn('export_user_id', self.ExportLog._fields)

    # ------------------------------------------------------------------
    # ExportLog model – metadata
    # ------------------------------------------------------------------

    def test_model_name(self):
        """_name must be 'export.log'."""
        self.assertEqual(self.ExportLog._name, 'export.log')

    def test_model_description(self):
        """_description must be set."""
        self.assertTrue(self.ExportLog._description)

    def test_rec_name_is_rec_name_field(self):
        """_rec_name must point to 'rec_name'."""
        self.assertEqual(self.ExportLog._rec_name, 'rec_name')

    # ------------------------------------------------------------------
    # ExportLog – direct record creation
    # ------------------------------------------------------------------

    def test_create_minimal_export_log(self):
        """Should create an export.log record with minimal fields."""
        rec = self.ExportLog.sudo().create({
            'rec_id': '1',
            'rec_name': 'Test Export',
        })
        self.assertTrue(rec.id)

    def test_create_full_export_log(self):
        """Should create a fully-populated export.log record."""
        rec = self.ExportLog.sudo().create({
            'rec_model_id': self.partner_ir_model.id,
            'rec_id': str(self.partner.id),
            'rec_name': self.partner.name,
            'exported_fields_ids': [(4, self.field_name.id),
                                    (4, self.field_email.id)],
        })
        self.assertTrue(rec.id)
        self.assertEqual(rec.rec_model_id, self.partner_ir_model)
        self.assertEqual(rec.rec_id, str(self.partner.id))
        self.assertIn(self.field_name, rec.exported_fields_ids)

    def test_export_date_default_set(self):
        """export_date should be automatically populated on creation."""
        rec = self.ExportLog.sudo().create({'rec_name': 'Auto Date'})
        self.assertTrue(rec.export_date)

    def test_export_user_id_default_is_current_user(self):
        """export_user_id should default to the current user."""
        rec = self.ExportLog.sudo().create({'rec_name': 'User Default'})
        self.assertEqual(rec.export_user_id, self.env.user)

    def test_display_name_uses_rec_name(self):
        """display_name should be derived from rec_name (_rec_name='rec_name')."""
        rec = self.ExportLog.sudo().create({'rec_name': 'Display Export'})
        self.assertIn('Display Export', rec.display_name)

    def test_search_by_rec_name(self):
        """export.log records should be searchable by rec_name."""
        self.ExportLog.sudo().create({'rec_name': 'FindableExport'})
        results = self.ExportLog.search([('rec_name', '=', 'FindableExport')])
        self.assertTrue(results)

    def test_exported_fields_ids_is_many2many(self):
        """exported_fields_ids should be a Many2many field."""
        from odoo import fields as odoo_fields
        field = self.ExportLog._fields['exported_fields_ids']
        self.assertIsInstance(field, odoo_fields.Many2many)

    def test_unlink_export_log(self):
        """export.log records should be deletable."""
        rec = self.ExportLog.sudo().create({'rec_name': 'To Delete Export'})
        rec_id = rec.id
        rec.sudo().unlink()
        self.assertFalse(self.ExportLog.browse(rec_id).exists())

    # ------------------------------------------------------------------
    # action_create_export_log
    # ------------------------------------------------------------------

    def _make_export_vals(self, rec_id=None, extra_fields=None):
        """Build a vals dict as the JS layer would send it."""
        rec_id = rec_id or self.partner.id
        export_list = [{'field_name': 'name'}]
        if extra_fields:
            export_list += [{'field_name': f} for f in extra_fields]
        return {
            'records': [{
                'rec_model': 'res.partner',
                'rec_id': rec_id,
            }],
            'exportList': export_list,
        }

    def test_action_create_export_log_creates_record(self):
        """action_create_export_log should create one export.log entry."""
        before = self.ExportLog.sudo().search_count([])
        self.ExportLog.sudo().action_create_export_log(
            self._make_export_vals())
        after = self.ExportLog.sudo().search_count([])
        self.assertEqual(after - before, 1)

    def test_action_create_export_log_stores_model(self):
        """The created export.log entry should store the correct ir.model."""
        self.ExportLog.sudo().action_create_export_log(
            self._make_export_vals())
        log = self.ExportLog.sudo().search(
            [('rec_id', '=', str(self.partner.id))], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_model_id.model, 'res.partner')

    def test_action_create_export_log_stores_rec_id(self):
        """The created export.log entry should store the correct rec_id."""
        self.ExportLog.sudo().action_create_export_log(
            self._make_export_vals())
        log = self.ExportLog.sudo().search(
            [('rec_id', '=', str(self.partner.id))], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_id, str(self.partner.id))

    def test_action_create_export_log_stores_rec_name(self):
        """The export.log entry should store the record's name."""
        self.ExportLog.sudo().action_create_export_log(
            self._make_export_vals())
        log = self.ExportLog.sudo().search(
            [('rec_id', '=', str(self.partner.id))], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_name, self.partner.name)

    def test_action_create_export_log_links_exported_fields(self):
        """The export.log entry should link the exported ir.model.fields."""
        self.ExportLog.sudo().action_create_export_log(
            self._make_export_vals())
        log = self.ExportLog.sudo().search(
            [('rec_id', '=', str(self.partner.id))], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertTrue(log.exported_fields_ids)
        exported_names = log.exported_fields_ids.mapped('name')
        self.assertIn('name', exported_names)

    def test_action_create_export_log_multiple_fields(self):
        """Exporting multiple fields should link all of them."""
        vals = self._make_export_vals(extra_fields=['email'])
        self.ExportLog.sudo().action_create_export_log(vals)
        log = self.ExportLog.sudo().search(
            [('rec_id', '=', str(self.partner.id))], order='id desc', limit=1)
        exported_names = log.exported_fields_ids.mapped('name')
        self.assertIn('name', exported_names)
        self.assertIn('email', exported_names)

    def test_action_create_export_log_multiple_records(self):
        """Exporting multiple records should create one export.log per record."""
        partner2 = self.env['res.partner'].search(
            [('is_company', '=', True), ('id', '!=', self.partner.id)],
            limit=1)
        if not partner2:
            partner2 = self.env['res.partner'].create({
                'name': 'Second Export Company',
                'is_company': True,
            })
        vals = {
            'records': [
                {'rec_model': 'res.partner', 'rec_id': self.partner.id},
                {'rec_model': 'res.partner', 'rec_id': partner2.id},
            ],
            'exportList': [{'field_name': 'name'}],
        }
        before = self.ExportLog.sudo().search_count([])
        self.ExportLog.sudo().action_create_export_log(vals)
        after = self.ExportLog.sudo().search_count([])
        self.assertEqual(after - before, 2)

    def test_action_create_export_log_empty_records_no_crash(self):
        """Passing an empty records list should not raise any error."""
        vals = {'records': [], 'exportList': [{'field_name': 'name'}]}
        try:
            self.ExportLog.sudo().action_create_export_log(vals)
        except Exception as e:
            self.fail(f"action_create_export_log raised unexpectedly: {e}")
