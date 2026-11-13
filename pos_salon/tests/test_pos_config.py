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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .common import TestSalonCommon


@tagged('post_install', '-at_install', 'pos_salon')
class TestPosConfig(TestSalonCommon):
    """Test suite for pos.config salon extensions."""

    __test__ = True

    def test_01_create_is_salon_defaults(self):
        """Creating a pos.config with is_salon=True should default show_appointments to True."""
        config_vals = {
            'name': 'POS Salon Create Test',
            'is_salon': True,
            'module_pos_restaurant': False,
        }
        if 'picking_type_id' in self.pos_config._fields and self.pos_config.picking_type_id:
            config_vals['picking_type_id'] = self.pos_config.picking_type_id.id
        if 'journal_id' in self.pos_config._fields and self.pos_config.journal_id:
            config_vals['journal_id'] = self.pos_config.journal_id.id

        config = self.env['pos.config'].create(config_vals)
        self.assertTrue(config.show_appointments)

    def test_02_write_is_salon_defaults(self):
        """Updating is_salon to True on an existing config should automatically enable show_appointments."""
        config_vals = {
            'name': 'POS Salon Write Test',
            'is_salon': False,
            'show_appointments': False,
            'module_pos_restaurant': False,
        }
        if 'picking_type_id' in self.pos_config._fields and self.pos_config.picking_type_id:
            config_vals['picking_type_id'] = self.pos_config.picking_type_id.id
        if 'journal_id' in self.pos_config._fields and self.pos_config.journal_id:
            config_vals['journal_id'] = self.pos_config.journal_id.id

        config = self.env['pos.config'].create(config_vals)
        self.assertFalse(config.show_appointments)

        # Write is_salon=True
        config.write({'is_salon': True})
        self.assertTrue(config.show_appointments)

    def test_03_salon_restaurant_conflict_constraint(self):
        """A POS config cannot have both is_salon and module_pos_restaurant enabled simultaneously."""
        with self.assertRaises(ValidationError):
            self.pos_config.write({
                'is_salon': True,
                'module_pos_restaurant': True,
            })

    def test_04_onchange_salon_restaurant_warning(self):
        """Simulating onchange when both is_salon and module_pos_restaurant are True returns a warning."""
        config = self.pos_config.new({
            'name': 'Onchange Test Config',
            'is_salon': True,
            'module_pos_restaurant': True,
        })
        res = config._onchange_salon_restaurant()
        self.assertIn('warning', res)
        self.assertEqual(res['warning']['title'], 'Not allowed')
