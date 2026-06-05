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


class TestDeleteLog(TransactionCase):
    """Test cases for DeleteLog model (delete.log) and
    BaseModel.unlink override."""

    def setUp(self):
        super().setUp()
        self.DeleteLog = self.env['delete.log']

        # Reuse the res.partner model as a tracked model for testing unlink
        self.partner_ir_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)

        # Set res.partner as a tracked model in ir.config_parameter
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids',
            str(self.partner_ir_model.ids)
        )

    def tearDown(self):
        # Clear the tracked models config after each test
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids', '')
        super().tearDown()

    # ------------------------------------------------------------------
    # DeleteLog model – field existence
    # ------------------------------------------------------------------

    def test_field_rec_model_id_exists(self):
        """rec_model_id field must be present on delete.log."""
        self.assertIn('rec_model_id', self.DeleteLog._fields)

    def test_field_rec_id_exists(self):
        """rec_id field must be present on delete.log."""
        self.assertIn('rec_id', self.DeleteLog._fields)

    def test_field_rec_name_exists(self):
        """rec_name field must be present on delete.log."""
        self.assertIn('rec_name', self.DeleteLog._fields)

    def test_field_delete_date_exists(self):
        """delete_date field must be present on delete.log."""
        self.assertIn('delete_date', self.DeleteLog._fields)

    def test_field_user_id_exists(self):
        """user_id field must be present on delete.log."""
        self.assertIn('user_id', self.DeleteLog._fields)

    # ------------------------------------------------------------------
    # DeleteLog model – metadata
    # ------------------------------------------------------------------

    def test_model_description(self):
        """_description must be set."""
        self.assertTrue(self.DeleteLog._description)

    def test_rec_name_is_rec_name_field(self):
        """_rec_name must point to 'rec_name'."""
        self.assertEqual(self.DeleteLog._rec_name, 'rec_name')

    # ------------------------------------------------------------------
    # DeleteLog – direct record creation
    # ------------------------------------------------------------------

    def test_create_minimal_delete_log(self):
        """Should create a delete.log record with minimal fields."""
        rec = self.DeleteLog.sudo().create({
            'rec_id': '99',
            'rec_name': 'Test Record',
        })
        self.assertTrue(rec.id)

    def test_create_full_delete_log(self):
        """Should create a fully-populated delete.log record."""
        rec = self.DeleteLog.sudo().create({
            'rec_model_id': self.partner_ir_model.id,
            'rec_id': '42',
            'rec_name': 'ACME Corp',
        })
        self.assertTrue(rec.id)
        self.assertEqual(rec.rec_model_id, self.partner_ir_model)
        self.assertEqual(rec.rec_id, '42')
        self.assertEqual(rec.rec_name, 'ACME Corp')

    def test_delete_date_default_set(self):
        """delete_date should be automatically populated on creation."""
        rec = self.DeleteLog.sudo().create({'rec_name': 'auto date test'})
        self.assertTrue(rec.delete_date)

    def test_user_id_default_is_current_user(self):
        """user_id should default to the current user."""
        rec = self.DeleteLog.sudo().create({'rec_name': 'user default test'})
        self.assertEqual(rec.user_id, self.env.user)

    def test_display_name_uses_rec_name(self):
        """display_name should be derived from rec_name (_rec_name='rec_name')."""
        rec = self.DeleteLog.sudo().create({'rec_name': 'Display Test'})
        self.assertIn('Display Test', rec.display_name)

    def test_search_by_rec_name(self):
        """delete.log records should be searchable by rec_name."""
        self.DeleteLog.sudo().create({'rec_name': 'SearchableRecord'})
        results = self.DeleteLog.search([('rec_name', '=', 'SearchableRecord')])
        self.assertTrue(results)

    def test_search_by_rec_id(self):
        """delete.log records should be searchable by rec_id."""
        self.DeleteLog.sudo().create({'rec_id': '12345', 'rec_name': 'ByID'})
        results = self.DeleteLog.search([('rec_id', '=', '12345')])
        self.assertTrue(results)

    # ------------------------------------------------------------------
    # BaseModel.unlink override – delete log creation
    # ------------------------------------------------------------------

    def test_unlink_tracked_model_creates_delete_log(self):
        """Deleting a record from a tracked model should create a delete.log
        entry."""
        partner = self.env['res.partner'].sudo().create({'name': 'Log On Delete'})
        before = self.DeleteLog.sudo().search_count([])
        partner.sudo().unlink()
        after = self.DeleteLog.sudo().search_count([])
        self.assertGreater(after, before,
                           "A delete.log record should have been created.")

    def test_unlink_tracked_model_stores_model_id(self):
        """The delete.log entry should store the correct ir.model reference."""
        partner = self.env['res.partner'].sudo().create({'name': 'Model ID Check'})
        partner_id = partner.id
        partner.sudo().unlink()
        log = self.DeleteLog.sudo().search(
            [('rec_id', '=', str(partner_id))], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_model_id.model, 'res.partner')

    def test_unlink_tracked_model_stores_record_name(self):
        """The delete.log entry should capture the display name before deletion."""
        partner = self.env['res.partner'].sudo().create(
            {'name': 'Name Before Delete'})
        partner_id = partner.id
        partner.sudo().unlink()
        log = self.DeleteLog.sudo().search(
            [('rec_id', '=', str(partner_id))], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_name, 'Name Before Delete')

    def test_unlink_tracked_model_stores_record_id(self):
        """The delete.log entry should store the correct rec_id (string of ID)."""
        partner = self.env['res.partner'].sudo().create({'name': 'ID Check'})
        partner_id = partner.id
        partner.sudo().unlink()
        log = self.DeleteLog.sudo().search(
            [('rec_id', '=', str(partner_id))], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.rec_id, str(partner_id))

    def test_unlink_untracked_model_does_not_create_delete_log(self):
        """Deleting a record from an untracked model should NOT create a
        delete.log entry."""
        # Use ir.rule (not in the tracked list) for deletion
        before = self.DeleteLog.sudo().search_count([])
        # Create an ir.attachment (non-tracked) and delete it
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Untracked Attachment',
            'datas': b'',
        })
        attachment.sudo().unlink()
        after = self.DeleteLog.sudo().search_count([])
        self.assertEqual(before, after,
                         "No delete.log record should have been created for "
                         "an untracked model.")

    def test_unlink_no_tracked_models_configured_skips_logging(self):
        """When no tracked models are configured, unlink should not create
        any delete.log entry."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids', '')
        partner = self.env['res.partner'].sudo().create({'name': 'No Config'})
        before = self.DeleteLog.sudo().search_count([])
        partner.sudo().unlink()
        after = self.DeleteLog.sudo().search_count([])
        self.assertEqual(before, after)

    def test_unlink_multiple_records_creates_log_for_each(self):
        """Unlinking multiple records at once should create one delete.log
        entry per record."""
        p1 = self.env['res.partner'].sudo().create({'name': 'Batch One'})
        p2 = self.env['res.partner'].sudo().create({'name': 'Batch Two'})
        before = self.DeleteLog.sudo().search_count([])
        (p1 | p2).sudo().unlink()
        after = self.DeleteLog.sudo().search_count([])
        self.assertEqual(after - before, 2)

    def test_unlink_delete_log_record_itself_is_not_tracked(self):
        """Deleting a delete.log record itself should not recursively create
        another delete.log (domain excludes 'delete.log' model)."""
        dummy = self.DeleteLog.sudo().create({'rec_name': 'Self Delete'})
        before = self.DeleteLog.sudo().search_count([])
        dummy.sudo().unlink()
        after = self.DeleteLog.sudo().search_count([])
        self.assertEqual(before - 1, after,
                         "Deleting a delete.log record should only reduce "
                         "the count by 1, not trigger a new log entry.")
