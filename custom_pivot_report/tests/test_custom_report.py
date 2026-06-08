# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################

from odoo.tests.common import TransactionCase

class TestCustomReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCustomReport, cls).setUpClass()
        
        # Find a model to test with
        cls.model_partner = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        
        # Find fields for that model
        cls.field_name = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.model_partner.id),
            ('name', '=', 'name')
        ], limit=1)
        
        cls.field_id = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.model_partner.id),
            ('name', '=', 'id')
        ], limit=1)
        
        cls.field_category = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.model_partner.id),
            ('name', '=', 'category_id')
        ], limit=1)
        
        # Create a parent menu
        cls.menu_parent = cls.env['ir.ui.menu'].create({
            'name': 'Test Parent Menu',
        })
        
        # Find a group to assign
        cls.group = cls.env.ref('base.group_user')

    def test_01_create_update_unlink_custom_report(self):
        """Test the full lifecycle of a custom report: creation, updating, and unlinking."""
        report = self.env['custom.report'].create({
            'name': 'Test Pivot Report',
            'model_id': self.model_partner.id,
            'menu_id': self.menu_parent.id,
            'menu_group_id': [(6, 0, [self.group.id])],
            'view_type': 'pivot',
            'fields_ids': [
                (0, 0, {
                    'custom_field_id': self.field_name.id,
                    'label': 'Name Label',
                    'row': True,
                }),
                (0, 0, {
                    'custom_field_id': self.field_id.id,
                    'label': 'ID Label',
                    'measure': True,
                }),
                (0, 0, {
                    'custom_field_id': self.field_category.id,
                    'label': 'Category Label',
                    # Neither row nor measure, just standard field
                })
            ]
        })
        
        # The identifiers created by the constraints
        expected_custom_report_view = f"{report.id}_{self.model_partner.model}_{self.menu_parent.complete_name}"
        expected_custom_report_action = f"{report.id}_pivot__current"
        expected_custom_report_menu = f"{report.id}_{self.menu_parent.complete_name}_{self.model_partner.model}"
        
        # --- Check View Creation ---
        view = self.env['ir.ui.view'].search([('custom_report', '=', expected_custom_report_view)])
        self.assertTrue(view, "Pivot view should be created automatically")
        self.assertEqual(view.model, 'res.partner')
        self.assertIn('<field name="name" type="row" string="Name Label"/>', view.arch_base)
        self.assertIn('<field name="id" type="measure" string="ID Label"/>', view.arch_base)
        self.assertIn('<field name="category_id" string="Category Label" />', view.arch_base)
        
        # --- Check Action Creation ---
        action = self.env['ir.actions.act_window'].search([('custom_report', '=', expected_custom_report_action)])
        self.assertTrue(action, "Window action should be created automatically")
        self.assertEqual(action.res_model, 'res.partner')
        self.assertEqual(action.view_id.id, view.id)
        
        # --- Check Menu Creation ---
        menu = self.env['ir.ui.menu'].search([('custom_report', '=', expected_custom_report_menu)])
        self.assertTrue(menu, "Menu item should be created automatically")
        self.assertEqual(menu.action.id, action.id)
        self.assertEqual(menu.parent_id.id, self.menu_parent.id)
        
        # --- Test Updating ---
        report.write({
            'name': 'Updated Pivot Report'
        })
        self.assertEqual(view.name, 'Updated Pivot Report', "View name should be updated")
        self.assertEqual(action.name, 'Updated Pivot Report', "Action name should be updated")
        self.assertEqual(menu.name, 'Updated Pivot Report', "Menu name should be updated")
        
        # --- Test Unlinking ---
        report.unlink()
        
        view_after = self.env['ir.ui.view'].search([('custom_report', '=', expected_custom_report_view)])
        self.assertFalse(view_after, "Pivot view should be deleted after unlink")
        
        action_after = self.env['ir.actions.act_window'].search([('custom_report', '=', expected_custom_report_action)])
        self.assertFalse(action_after, "Action should be deleted after unlink")
        
        menu_after = self.env['ir.ui.menu'].search([('custom_report', '=', expected_custom_report_menu)])
        self.assertFalse(menu_after, "Menu should be deleted after unlink")

    def test_02_onchange_custom_field_id(self):
        """Test the onchange behavior of custom.report.fields"""
        field_obj = self.env['custom.report.fields'].new({
            'custom_field_id': self.field_id.id,
        })
        field_obj.onchange_custom_field_id()
        
        # 'id' field is an integer type, so measurable should become True
        self.assertTrue(field_obj.measurable, "Integer field should be measurable")
        self.assertEqual(field_obj.label, self.field_id.field_description)
        
        # test a many2many field
        field_obj_m2m = self.env['custom.report.fields'].new({
            'custom_field_id': self.field_category.id, # category_id is usually a many2many
        })
        field_obj_m2m.onchange_custom_field_id()
        self.assertTrue(field_obj_m2m.rowable, "Many2many field should be rowable")
