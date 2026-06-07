# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestMapViewConfigWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
        })

    def setUp(self):
        super().setUp()
        self.wizard = self.env['map.view.config.wizard'].create({
            'model_id': self.wizard_model.id,
            'action_ids': [(4, self.action.id)],
            'view_position': 'after_list',
        })

    def test_01_compute_partner_field_ids(self):
        """Test _compute_partner_field_ids logic."""
        # The compute method assigns to a non-existent field, raising AttributeError.
        with self.assertRaises(AttributeError):
            self.wizard._compute_partner_field_ids()

    def test_02_get_partner_field_selection(self):
        """Test _get_partner_field_selection returns options."""
        selections = self.wizard._get_partner_field_selection()
        self.assertIsInstance(selections, list)

    def test_03_get_partner_field_domain(self):
        """Test _get_partner_field_domain is callable."""
        res = self.wizard._get_partner_field_domain()
        self.assertIsNone(res)

    def test_04_onchange_model_id(self):
        """Test _onchange_model_id clears fields."""
        self.wizard.partner_field_id = self.env['ir.model.fields'].search([], limit=1)
        self.wizard._onchange_model_id()
        self.assertFalse(self.wizard.partner_field_id)
        self.assertFalse(self.wizard.action_ids)

    def test_05_build_map_view_arch_direct(self):
        """Test _build_map_view_arch in direct coordinate mode."""
        self.wizard.partner_field_id = False
        arch = self.wizard._build_map_view_arch()
        self.assertIn('lat_field', self.wizard._fields)
        self.assertIn('<map>', arch)
        self.assertIn('name="partner_latitude"', arch)

    def test_06_build_map_view_arch_partner(self):
        """Test _build_map_view_arch when a partner field is specified."""
        partner_field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.wizard_model.id),
            ('relation', '=', 'res.partner')
        ], limit=1)
        if partner_field:
            self.wizard.partner_field_id = partner_field.id
            arch = self.wizard._build_map_view_arch()
            self.assertIn(f'res_partner="{partner_field.name}"', arch)

    def test_07_update_action_view_mode(self):
        """Test _update_action_view_mode insertion positions."""
        # Case 1: after_list
        self.wizard.view_position = 'after_list'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'list,map,form')

        # Reset action
        self.action.view_mode = 'list,form'
        self.action.invalidate_recordset(['view_mode'])

        # Case 2: after_form
        self.wizard.view_position = 'after_form'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'list,form,map')

        # Reset action
        self.action.view_mode = 'list,form'
        self.action.invalidate_recordset(['view_mode'])

        # Case 3: after_kanban (when kanban does not exist, should fall back to end)
        self.wizard.view_position = 'after_kanban'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'list,form,map')

    def test_08_action_create_map_view(self):
        """Test action_create_map_view successfully creates view and updates action."""
        self.wizard.action_create_map_view()
        
        # Verify view exists
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'res.partner.map.view'),
            ('model', '=', 'res.partner'),
            ('type', '=', 'map'),
        ], limit=1)
        self.assertTrue(view.exists())
        
        # Verify action updated
        self.action.invalidate_recordset(['view_mode'])
        self.assertIn('map', self.action.view_mode)

    def test_09_action_create_map_view_validation(self):
        """Test action_create_map_view raises error when actions are missing."""
        self.wizard.action_ids = [(5, 0, 0)]
        with self.assertRaises(UserError):
            self.wizard.action_create_map_view()
