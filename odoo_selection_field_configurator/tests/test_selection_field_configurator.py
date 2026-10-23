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
#############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSelectionFieldConfigurator(TransactionCase):
    """ Test suite for Odoo Selection Field Configurator:
    Verifies dynamic option creation, label modification, value updates,
    core option protection, deletion, and schema safeguards. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_type_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'type'),
        ], limit=1)

    def test_01_add_custom_selection_option(self):
        """ Test adding a custom selection option to a base selection field. """
        custom_opt = self.env['ir.model.fields.selection'].create({
            'field_id': self.partner_type_field.id,
            'value': 'custom_delivery_hub',
            'name': 'Delivery Hub',
            'sequence': 50,
        })
        self.assertTrue(custom_opt.id, "Custom selection option should be created.")
        self.assertFalse(custom_opt._is_core_selection(), "Option must be identified as custom.")

        field = self.env['res.partner']._fields['type']
        self.assertIn('custom_delivery_hub', field._selection,
                      "Custom option must be present in field._selection cache.")

        descriptions = dict(field._description_selection(self.env))
        self.assertIn('custom_delivery_hub', descriptions,
                      "Custom option must be present in _description_selection.")
        self.assertEqual(descriptions['custom_delivery_hub'], 'Delivery Hub')

        # Create record with custom option
        partner = self.env['res.partner'].create({
            'name': 'Test Partner Hub',
            'type': 'custom_delivery_hub',
        })
        self.assertEqual(partner.type, 'custom_delivery_hub',
                         "Partner record should accept and persist custom selection value.")

    def test_02_modify_custom_selection_label(self):
        """ Test updating the display label of a custom selection option. """
        custom_opt = self.env['ir.model.fields.selection'].create({
            'field_id': self.partner_type_field.id,
            'value': 'warehouse_depot',
            'name': 'Warehouse Depot',
            'sequence': 55,
        })
        custom_opt.write({'name': 'Regional Warehouse Depot'})

        descriptions = dict(self.env['res.partner']._fields['type']._description_selection(self.env))
        self.assertEqual(descriptions['warehouse_depot'], 'Regional Warehouse Depot',
                         "Display label must be updated in _description_selection.")

    def test_03_modify_custom_selection_value(self):
        """ Test updating the technical value of a custom selection option.
        Existing records must have their column values updated in PostgreSQL. """
        custom_opt = self.env['ir.model.fields.selection'].create({
            'field_id': self.partner_type_field.id,
            'value': 'old_hub_val',
            'name': 'Hub Center',
            'sequence': 60,
        })
        partner = self.env['res.partner'].create({
            'name': 'Test Hub Partner',
            'type': 'old_hub_val',
        })
        self.assertEqual(partner.type, 'old_hub_val')

        # Update technical value
        custom_opt.write({'value': 'new_hub_val'})

        # Invalidate cache to read from DB column
        partner.invalidate_recordset(['type'])
        self.assertEqual(partner.type, 'new_hub_val',
                         "Existing database records must be updated when selection value changes.")

    def test_04_protect_core_selection_value(self):
        """ Test that attempting to modify the technical value of a core selection option is forbidden. """
        core_opt = self.env['ir.model.fields.selection'].search([
            ('field_id', '=', self.partner_type_field.id),
            ('value', '=', 'contact'),
        ], limit=1)
        self.assertTrue(core_opt, "Core option 'contact' should exist.")
        self.assertTrue(core_opt._is_core_selection(), "'contact' must be recognized as core.")

        with self.assertRaises(UserError) as err:
            core_opt.write({'value': 'primary_contact'})
        self.assertIn("core/system selection options cannot be modified", str(err.exception))

    def test_05_protect_core_selection_deletion(self):
        """ Test that core selection options cannot be deleted. """
        core_opt = self.env['ir.model.fields.selection'].search([
            ('field_id', '=', self.partner_type_field.id),
            ('value', '=', 'invoice'),
        ], limit=1)
        self.assertTrue(core_opt, "Core option 'invoice' should exist.")

        with self.assertRaises(UserError) as err:
            core_opt.unlink()
        self.assertIn("cannot be deleted", str(err.exception))

    def test_06_delete_custom_selection_option(self):
        """ Test that custom-added selection options can be deleted cleanly. """
        custom_opt = self.env['ir.model.fields.selection'].create({
            'field_id': self.partner_type_field.id,
            'value': 'temporary_branch',
            'name': 'Temporary Branch',
            'sequence': 70,
        })
        self.assertIn('temporary_branch', self.env['res.partner']._fields['type']._selection)

        custom_opt.unlink()
        self.assertNotIn('temporary_branch', self.env['res.partner']._fields['type']._selection,
                         "Deleted option must be removed from field._selection.")

    def test_07_ir_model_fields_write_selection_ids(self):
        """ Test writing selection_ids directly on ir.model.fields form/write. """
        self.partner_type_field.write({
            'selection_ids': [(0, 0, {
                'value': 'express_terminal',
                'name': 'Express Terminal',
                'sequence': 80,
            })]
        })
        field = self.env['res.partner']._fields['type']
        self.assertIn('express_terminal', field._selection,
                      "Writing selection_ids on base ir.model.fields must register the new option.")

    def test_08_ir_model_fields_prevent_base_field_alteration(self):
        """ Test that attempting to modify core base field properties (like renaming) is still strictly forbidden. """
        with self.assertRaises(UserError):
            self.partner_type_field.write({'name': 'altered_field_name'})
