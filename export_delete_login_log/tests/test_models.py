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
class TestBaseModelUnlink(TransactionCase):
    """Test cases for the overridden unlink method in models.py (base model).

    The BaseModel extends 'base' and creates a delete.log record when a
    record belonging to a tracked model is deleted.
    """

    def setUp(self):
        super().setUp()
        # We'll use res.partner as a representative tracked model
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)

    def _set_tracked_models(self, model_ids):
        """Helper: set the tracked model IDs in ir.config_parameter."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids',
            str(model_ids)
        )

    def _clear_tracked_models(self):
        """Helper: clear the tracked models setting."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids', ''
        )

    def test_unlink_creates_delete_log_when_model_tracked(self):
        """Unlink on a tracked model should create a delete.log entry."""
        self._set_tracked_models([self.partner_model.id])

        partner = self.env['res.partner'].create({'name': 'To Be Deleted'})
        partner_id = partner.id
        partner_name = partner.name

        before_count = self.env['delete.log'].sudo().search_count([])
        partner.unlink()
        after_count = self.env['delete.log'].sudo().search_count([])

        self.assertEqual(
            after_count, before_count + 1,
            "A delete.log entry should be created when a tracked model record is deleted."
        )

    def test_unlink_delete_log_has_correct_model(self):
        """The delete.log entry should reference the correct ir.model."""
        self._set_tracked_models([self.partner_model.id])

        partner = self.env['res.partner'].create({'name': 'Partner For Model Check'})
        partner.unlink()

        latest_log = self.env['delete.log'].sudo().search(
            [], order='id desc', limit=1)
        self.assertEqual(
            latest_log.rec_model.id, self.partner_model.id,
            "delete.log rec_model should reference the deleted record's model."
        )

    def test_unlink_does_not_create_delete_log_when_model_not_tracked(self):
        """Unlink on an untracked model should NOT create a delete.log entry."""
        # Make sure res.partner is NOT in the tracked models list
        self._set_tracked_models([])

        partner = self.env['res.partner'].create({'name': 'Untracked Partner'})
        before_count = self.env['delete.log'].sudo().search_count([])
        partner.unlink()
        after_count = self.env['delete.log'].sudo().search_count([])

        self.assertEqual(
            before_count, after_count,
            "No delete.log entry should be created for an untracked model."
        )

    def test_unlink_does_not_create_delete_log_when_no_tracked_models(self):
        """When no tracked models are configured, unlink should not log deletions."""
        self._clear_tracked_models()

        partner = self.env['res.partner'].create({'name': 'No Track Partner'})
        before_count = self.env['delete.log'].sudo().search_count([])
        partner.unlink()
        after_count = self.env['delete.log'].sudo().search_count([])

        self.assertEqual(
            before_count, after_count,
            "No delete.log entry should be created when tracked_models param is empty."
        )

    def test_unlink_still_deletes_the_record(self):
        """Unlink should delete the record even when logging is active."""
        self._set_tracked_models([self.partner_model.id])

        partner = self.env['res.partner'].create({'name': 'Must Be Deleted'})
        partner_id = partner.id
        partner.unlink()

        remaining = self.env['res.partner'].sudo().search([('id', '=', partner_id)])
        self.assertFalse(
            remaining.exists(),
            "The partner record should be deleted after unlink() is called."
        )

    def test_unlink_multiple_records_tracked(self):
        """When multiple records of a tracked model are deleted, each should create a log."""
        self._set_tracked_models([self.partner_model.id])

        partners = self.env['res.partner'].create([
            {'name': 'Delete Multi 1'},
            {'name': 'Delete Multi 2'},
        ])
        before_count = self.env['delete.log'].sudo().search_count([])
        # Unlink individually so each triggers the loop
        for partner in partners:
            partner.unlink()
        after_count = self.env['delete.log'].sudo().search_count([])

        self.assertEqual(
            after_count, before_count + 2,
            "Each deleted tracked record should produce its own delete.log entry."
        )

    def test_base_model_inherit(self):
        """Confirm the overridden unlink is on the 'base' abstract model."""
        base_model = self.env['base']
        self.assertTrue(
            hasattr(base_model, 'unlink'),
            "'base' model should have an 'unlink' method."
        )
