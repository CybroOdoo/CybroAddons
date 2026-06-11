# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError


class TestExportAttachment(TransactionCase):
    """Test cases for the ExportAttachment model (export.attachment).

    We use res.users as the target model for window-action bindings to avoid
    enterprise-specific NOT NULL constraints that res.partner may carry
    (e.g. autopost_bills from the account module).
    """

    def setUp(self):
        super().setUp()
        # Use res.users – always present, no complex constraints
        self.target_model = self.env['ir.model']._get('res.users')
        self.export_attachment = self.env['export.attachment'].create({
            'action_name': 'Test Export Action',
            'applied_model_id': self.target_model.id,
        })

    # ------------------------------------------------------------------
    # 1. Record creation & default values
    # ------------------------------------------------------------------

    def test_01_record_creation(self):
        """ExportAttachment record should be created with correct values."""
        self.assertTrue(
            self.export_attachment.id,
            "ExportAttachment record should have been created."
        )
        self.assertEqual(self.export_attachment.action_name,
                         'Test Export Action')
        self.assertEqual(self.export_attachment.applied_model_id,
                         self.target_model)

    def test_02_default_state_is_draft(self):
        """Default state for a new record should be 'draft'."""
        self.assertEqual(
            self.export_attachment.states,
            'draft',
            "Default state should be 'draft'.",
        )

    def test_03_default_enabled_value_is_true(self):
        """enabled_value should default to True on new records."""
        self.assertTrue(
            self.export_attachment.enabled_value,
            "enabled_value should default to True.",
        )

    def test_04_default_act_window_id_is_empty(self):
        """act_window_id should be empty on a newly created record."""
        self.assertFalse(
            self.export_attachment.act_window_id,
            "act_window_id should be empty before action_create is called.",
        )

    # ------------------------------------------------------------------
    # 2. _compute_created_action_names
    # ------------------------------------------------------------------

    def test_05_compute_created_action_names_no_matching_action(self):
        """Computed field should be empty when no window action matches."""
        record = self.env['export.attachment'].create({
            'action_name': 'NonExistentActionXYZ_99',
        })
        self.assertEqual(
            record.created_action_names,
            '',
            "created_action_names should be empty when no window action exists.",
        )

    def test_06_compute_created_action_names_with_matching_action(self):
        """Computed field should list the action name when a matching
        ir.actions.act_window exists."""
        action_name = 'MatchingWindowAction_TestCase'
        self.env['ir.actions.act_window'].create({
            'name': action_name,
            'res_model': 'res.users',
            'view_mode': 'list',
        })
        record = self.env['export.attachment'].create({
            'action_name': action_name,
        })
        self.assertIn(
            action_name,
            record.created_action_names,
            "created_action_names should contain the matching action name.",
        )

    # ------------------------------------------------------------------
    # 3. action_create
    # ------------------------------------------------------------------

    def test_07_action_create_sets_state_to_running(self):
        """action_create() should transition the state to 'running'."""
        self.export_attachment.action_create()
        self.assertEqual(self.export_attachment.states, 'running')

    def test_08_action_create_disables_enabled_value(self):
        """action_create() should set enabled_value to False."""
        self.export_attachment.action_create()
        self.assertFalse(self.export_attachment.enabled_value)

    def test_09_action_create_creates_act_window(self):
        """action_create() should create an ir.actions.act_window and link it."""
        self.export_attachment.action_create()
        self.assertTrue(self.export_attachment.act_window_id)
        window_action = self.export_attachment.act_window_id
        self.assertEqual(window_action.name, 'Test Export Action')
        self.assertEqual(
            window_action.res_model,
            'attachment.download.confirmation',
        )

    def test_10_action_create_window_binding_model(self):
        """The created window action should be bound to the applied model."""
        self.export_attachment.action_create()
        window_action = self.export_attachment.act_window_id
        self.assertEqual(
            window_action.binding_model_id,
            self.target_model,
            "Window action should be bound to the applied model.",
        )

    def test_11_action_create_window_binding_view_types(self):
        """The created window action should be bound to list views."""
        self.export_attachment.action_create()
        self.assertEqual(
            self.export_attachment.act_window_id.binding_view_types,
            'list',
        )

    def test_12_action_create_window_target_is_new(self):
        """The created window action target should be 'new'."""
        self.export_attachment.action_create()
        self.assertEqual(
            self.export_attachment.act_window_id.target,
            'new',
        )

    # ------------------------------------------------------------------
    # 4. action_unlink
    # ------------------------------------------------------------------

    def test_13_action_unlink_sets_state_to_cancel(self):
        """action_unlink() should transition the state to 'cancel'."""
        self.export_attachment.action_create()
        self.export_attachment.action_unlink()
        self.assertEqual(self.export_attachment.states, 'cancel')

    def test_14_action_unlink_re_enables_enabled_value(self):
        """action_unlink() should reset enabled_value to True."""
        self.export_attachment.action_create()
        self.export_attachment.action_unlink()
        self.assertTrue(self.export_attachment.enabled_value)

    def test_15_action_unlink_removes_act_window(self):
        """action_unlink() should delete the linked ir.actions.act_window."""
        self.export_attachment.action_create()
        window_action_id = self.export_attachment.act_window_id.id
        self.export_attachment.action_unlink()
        remaining = self.env['ir.actions.act_window'].search(
            [('id', '=', window_action_id)]
        )
        self.assertFalse(
            remaining,
            "The ir.actions.act_window should be deleted after action_unlink.",
        )

    def test_16_action_unlink_returns_reload_client_action(self):
        """action_unlink() should return a client action with tag 'reload'."""
        self.export_attachment.action_create()
        result = self.export_attachment.action_unlink()
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    # ------------------------------------------------------------------
    # 5. Field constraints & misc
    # ------------------------------------------------------------------

    def test_17_action_name_is_required(self):
        """Creating an ExportAttachment without action_name should fail."""
        with self.assertRaises(Exception):
            self.env['export.attachment'].create({
                'applied_model_id': self.target_model.id,
            })

    def test_18_rec_name_uses_action_name(self):
        """The display name of the record should be the action_name."""
        self.assertEqual(
            self.export_attachment.display_name,
            'Test Export Action',
        )

    def test_19_multiple_records_independent_states(self):
        """Multiple ExportAttachment records should manage state independently."""
        record2 = self.env['export.attachment'].create({
            'action_name': 'Second Action',
            'applied_model_id': self.target_model.id,
        })
        self.export_attachment.action_create()
        # record2 should still be in draft
        self.assertEqual(record2.states, 'draft')
        # self.export_attachment should be running
        self.assertEqual(self.export_attachment.states, 'running')

    def test_20_action_create_without_applied_model(self):
        """action_create() with no applied_model_id should still create a
        window action (binding_model_id will be False/unset)."""
        record = self.env['export.attachment'].create({
            'action_name': 'No Model Action',
        })
        record.action_create()
        self.assertTrue(
            record.act_window_id,
            "Window action should be created even without an applied_model_id.",
        )
        self.assertFalse(
            record.act_window_id.binding_model_id,
            "binding_model_id should be unset when no applied_model_id given.",
        )

    def test_21_state_selection_values(self):
        """State field should only allow 'draft', 'running', or 'cancel'."""
        valid_states = ['draft', 'running', 'cancel']
        field_selection = dict(
            self.env['export.attachment']._fields['states'].selection
        )
        for state in valid_states:
            self.assertIn(state, field_selection)

    def test_22_act_window_id_is_readonly(self):
        """act_window_id field should be marked as readonly."""
        field = self.env['export.attachment']._fields['act_window_id']
        self.assertTrue(
            field.readonly,
            "act_window_id should be a readonly field.",
        )
