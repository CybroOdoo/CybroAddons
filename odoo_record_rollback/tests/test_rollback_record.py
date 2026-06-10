# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
import json
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestRollbackRecord(TransactionCase):
    """Test suite for the rollback.record model covering get_models(),
    action_record_selection(), and field defaults."""

    def setUp(self):
        super().setUp()
        # Locate ir.model entry for res.partner to use as a test model
        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        # Configure the module to track res.partner
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids',
            str(self.partner_model.ids))

    # ------------------------------------------------------------------
    # get_models()
    # ------------------------------------------------------------------

    def test_get_models_returns_list(self):
        """get_models() must always return a list (never None or False)."""
        result = self.env['rollback.record'].get_models()
        self.assertIsInstance(result, list,
                              "get_models() should return a list")

    def test_get_models_returns_configured_model(self):
        """get_models() returns the model technical name for each configured
        ir.model record."""
        models_list = self.env['rollback.record'].get_models()
        self.assertIn('res.partner', models_list,
                      "res.partner should be in the configured rollback models")

    def test_get_models_empty_when_no_param(self):
        """get_models() returns an empty list when the config parameter is
        absent or blank."""
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids', False)
        result = self.env['rollback.record'].get_models()
        self.assertEqual(result, [],
                         "get_models() should return [] when param is unset")

    def test_get_models_empty_list_param(self):
        """get_models() handles an explicitly empty list '[]' gracefully."""
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids', '[]')
        result = self.env['rollback.record'].get_models()
        self.assertEqual(result, [],
                         "get_models() should return [] for an empty list param")

    def test_get_models_invalid_param_falls_back(self):
        """get_models() returns an empty list when the param value is corrupt
        / cannot be parsed."""
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids', 'NOT_VALID_PYTHON')
        result = self.env['rollback.record'].get_models()
        self.assertEqual(result, [],
                         "get_models() should return [] for an unparseable param")

    def test_get_models_multiple_models(self):
        """get_models() returns multiple model names when several models are
        configured."""
        user_model = self.env['ir.model'].search(
            [('model', '=', 'res.users')], limit=1)
        ids = self.partner_model.ids + user_model.ids
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids', str(ids))
        result = self.env['rollback.record'].get_models()
        self.assertIn('res.partner', result)
        self.assertIn('res.users', result)

    # ------------------------------------------------------------------
    # Default field values
    # ------------------------------------------------------------------

    def test_default_user_id(self):
        """A newly created rollback.record carries the current user as
        user_id."""
        record = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': 1,
            'history': '{}',
        })
        self.assertEqual(record.user_id, self.env.user,
                         "user_id default should be the current user")

    def test_default_write_time_set(self):
        """write_time is automatically populated on creation."""
        record = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': 1,
            'history': '{}',
        })
        self.assertTrue(record.write_time,
                        "write_time should be set automatically on creation")

    # ------------------------------------------------------------------
    # action_record_selection()
    # ------------------------------------------------------------------

    def test_action_record_selection_restores_value(self):
        """action_record_selection() writes the stored history back onto the
        target record, effectively restoring it to its prior state."""
        # Create a partner with a known name
        partner = self.env['res.partner'].create({'name': 'Original Name'})
        original_name = partner.name

        # Manually build a rollback entry representing the prior state
        rollback_entry = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': partner.id,
            'history': json.dumps({'name': original_name}),
        })

        # Change the partner name so it differs from history
        partner.write({'name': 'Changed Name'})
        self.assertEqual(partner.name, 'Changed Name')

        # Apply the rollback — should restore the original name
        result = rollback_entry.action_record_selection()
        self.assertEqual(partner.name, original_name,
                         "Rollback should restore the partner name to its "
                         "original value")

    def test_action_record_selection_returns_client_action(self):
        """action_record_selection() returns a client action dict with
        tag='reload'."""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        rollback_entry = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': partner.id,
            'history': json.dumps({'name': 'Test Partner'}),
        })
        result = rollback_entry.action_record_selection()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    def test_action_record_selection_multiple_fields(self):
        """action_record_selection() can restore multiple field values at
        once from a single history entry."""
        partner = self.env['res.partner'].create({
            'name': 'Multi Field Partner',
            'phone': '+1-111-111-1111',
        })
        history = json.dumps({
            'name': 'Multi Field Partner',
            'phone': '+1-111-111-1111',
        })
        rollback_entry = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': partner.id,
            'history': history,
        })
        # Modify both fields
        partner.write({'name': 'Modified Name', 'phone': '+9-999-999-9999'})
        # Rollback
        rollback_entry.action_record_selection()
        self.assertEqual(partner.name, 'Multi Field Partner')
        self.assertEqual(partner.phone, '+1-111-111-1111')

    # ------------------------------------------------------------------
    # Record fields
    # ------------------------------------------------------------------

    def test_rollback_record_fields_stored_correctly(self):
        """res_model, record, and history are stored and retrievable."""
        history_data = json.dumps({'name': 'Some Name'})
        entry = self.env['rollback.record'].create({
            'res_model': 'res.partner',
            'record': 42,
            'history': history_data,
        })
        self.assertEqual(entry.res_model, 'res.partner')
        self.assertEqual(entry.record, 42)
        self.assertEqual(entry.history, history_data)
