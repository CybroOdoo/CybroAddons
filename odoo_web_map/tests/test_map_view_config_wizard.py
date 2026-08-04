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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestMapViewConfigWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.action = self.env['ir.actions.act_window'].create({
            'name': 'Test Partners',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
        })
        self.wizard = self.env['map.view.config.wizard'].create({
            'model_id': self.model.id,
            'action_ids': [(4, self.action.id)],
            'view_position': 'after_form',
        })

    def test_01_compute_partner_field_ids(self):
        """ Test computation of partner fields """
        self.wizard._compute_partner_field_ids()
        self.assertTrue(self.wizard.partner_field_ids)
        self.assertIn('parent_id', self.wizard.partner_field_ids.mapped('name'))

    def test_03_onchange_model_id(self):
        """ Test onchange clears fields """
        wizard = self.env['map.view.config.wizard'].new({
            'model_id': self.model.id,
            'action_ids': [(4, self.action.id)],
        })
        wizard.partner_field_id = self.env['ir.model.fields'].search([], limit=1)
        
        # Simulate change
        wizard._onchange_model_id()
        self.assertFalse(wizard.action_ids)
        self.assertFalse(wizard.partner_field_id)

    def test_04_build_map_view_arch(self):
        """ Test Map XML Architecture Generation """
        # Default architecture
        arch = self.wizard._build_map_view_arch()
        self.assertIn('<map>', arch)
        self.assertIn('<field name="display_name"/>', arch)
        # Should not have any attributes since it's defaulting to partner_latitude, contact_address etc which are omited
        
        # Test with custom fields
        self.wizard.lat_field = 'custom_lat'
        self.wizard.lng_field = 'custom_lng'
        self.wizard.address_field = 'custom_address'
        
        arch2 = self.wizard._build_map_view_arch()
        self.assertIn('lat_field="custom_lat"', arch2)
        self.assertIn('lng_field="custom_lng"', arch2)
        self.assertIn('address_field="custom_address"', arch2)

    def test_05_update_action_view_mode(self):
        """ Test updating action view mode string """
        # after_form test (action currently 'tree,form')
        self.wizard.view_position = 'after_form'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'tree,form,map')

        # after_list test
        self.action.view_mode = 'tree,form'
        self.wizard.view_position = 'after_list'
        # Note: in view_modes list is 'list', but action is 'tree' in setup? Wait, the wizard checks 'list'. 
        # tree vs list might be tricky but we test 'list' inside view_mode explicitly if possible.
        self.action.view_mode = 'list,form'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'list,map,form')

        # end test
        self.wizard.view_position = 'end'
        self.wizard._update_action_view_mode(self.action)
        self.assertEqual(self.action.view_mode, 'list,form,map')

    def test_06_action_create_map_view(self):
        """ Test full creation string """
        # It creates an ir.ui.view and updates actions
        self.wizard.action_create_map_view()
        
        # Verify View was created
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'res.partner.map.view'),
            ('model', '=', 'res.partner'),
            ('type', '=', 'map')
        ])
        self.assertEqual(len(view), 1)
        self.assertIn('<map>', view.arch)
        
        # Verify Action was updated
        self.action.invalidate_recordset(['view_mode'])
        self.assertEqual(self.action.view_mode, 'tree,form,map')
