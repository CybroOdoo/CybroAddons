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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMultiFollower(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fetch an ir.model to use as the target for actions
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        cls.follower = cls.env['multi.follower'].create({
            'action_name': 'Test Add Followers',
            'applied_to_ids': [(6, 0, cls.partner_model.ids)],
        })

    def test_default_state_and_enabled(self):
        """Test that a new multi.follower record defaults to draft state."""
        self.assertEqual(self.follower.states, 'draft')
        self.assertTrue(self.follower.enabled_value)

    def test_compute_created_action_names_empty(self):
        """Test _compute_created_action_names returns empty when no actions linked."""
        self.follower._compute_created_action_names()
        self.assertFalse(self.follower.created_action_names)

    def test_action_create(self):
        """Test action_create creates window actions and transitions state."""
        result = self.follower.action_create()

        # State should be set to running
        self.assertEqual(self.follower.states, 'running')
        # enabled_value should be False (action created)
        self.assertFalse(self.follower.enabled_value)
        # A window action should have been created per applied model
        self.assertTrue(self.follower.window_action_ids,
                        "Window actions should be created after action_create.")
        self.assertEqual(len(self.follower.window_action_ids),
                         len(self.follower.applied_to_ids),
                         "One window action should be created per applied model.")
        # The created action must carry the correct name
        for action in self.follower.window_action_ids:
            self.assertEqual(action.name, 'Test Add Followers')
            self.assertEqual(action.res_model, 'follower.adding.removing')
            self.assertEqual(action.binding_model_id.id, self.partner_model.id)
        # Return value must be a reload client action
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    def test_compute_created_action_names_after_create(self):
        """Test _compute_created_action_names returns names after action_create."""
        self.follower.action_create()
        self.follower._compute_created_action_names()
        self.assertIn('Test Add Followers', self.follower.created_action_names)

    def test_action_unlink(self):
        """Test action_unlink removes window actions and resets state."""
        self.follower.action_create()
        self.assertTrue(self.follower.window_action_ids)

        result = self.follower.action_unlink()

        self.assertEqual(self.follower.states, 'cancel')
        self.assertTrue(self.follower.enabled_value)
        self.assertFalse(self.follower.window_action_ids,
                         "Window actions should be cleared after action_unlink.")
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    def test_unlink_cleans_up_actions(self):
        """Test that deleting a multi.follower removes its window actions first."""
        follower = self.env['multi.follower'].create({
            'action_name': 'Temp Follower Action',
            'applied_to_ids': [(6, 0, self.partner_model.ids)],
        })
        follower.action_create()
        action_ids = follower.window_action_ids.ids
        self.assertTrue(action_ids, "Actions should exist before unlink.")

        follower.unlink()

        # Window actions should have been deleted
        remaining = self.env['ir.actions.act_window'].search(
            [('id', 'in', action_ids)])
        self.assertFalse(remaining,
                         "Window actions should be deleted when the follower is unlinked.")

    def test_multi_recordset_action_create_and_unlink(self):
        """Test action_create and action_unlink on a multi-record recordset."""
        followers = self.env['multi.follower'].create([
            {
                'action_name': 'Multi Record Action 1',
                'applied_to_ids': [(6, 0, self.partner_model.ids)],
            },
            {
                'action_name': 'Multi Record Action 2',
                'applied_to_ids': [(6, 0, self.partner_model.ids)],
            },
        ])
        self.assertEqual(len(followers), 2)
        # Test batch create
        followers.action_create()
        for rec in followers:
            self.assertEqual(rec.states, 'running')
            self.assertFalse(rec.enabled_value)
            self.assertTrue(rec.window_action_ids)

        # Test batch unlink
        followers.action_unlink()
        for rec in followers:
            self.assertEqual(rec.states, 'cancel')
            self.assertTrue(rec.enabled_value)
            self.assertFalse(rec.window_action_ids)

    def test_applied_to_ids_domain(self):
        """Test that applied_to_ids field has domain restricting to is_mail_thread models."""
        field = self.env['multi.follower']._fields['applied_to_ids']
        self.assertEqual(field.domain, "[('is_mail_thread', '=', True)]")
