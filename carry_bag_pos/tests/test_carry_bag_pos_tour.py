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
from odoo import Command
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import (
    TestPointOfSaleHttpCommon,
)


@tagged('post_install', '-at_install')
class TestCarryBagPosTour(TestPointOfSaleHttpCommon):
    """Run the 'Add Bag' flow through the real POS user interface."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        bag_category = cls.env['pos.category'].create({'name': 'Carry Bags'})
        other_category = cls.env['pos.category'].create({'name': 'Others'})
        cls.env['product.template'].create({
            'name': 'Test Carry Bag',
            'available_in_pos': True,
            'list_price': 0.50,
            'taxes_id': [Command.clear()],
            'pos_categ_ids': [Command.set(bag_category.ids)],
        })
        cls.env['product.template'].create({
            'name': 'Test Other Product',
            'available_in_pos': True,
            'list_price': 3.00,
            'taxes_id': [Command.clear()],
            'pos_categ_ids': [Command.set(other_category.ids)],
        })
        cls.main_pos_config.write({
            'is_bag_charges': True,
            'bag_category_id': bag_category.id,
        })

    def test_add_bag_tour(self):
        """The bag popup lists only bag products and adds the selected one
        to the order through the standard POS order line flow."""
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour('carry_bag_pos_tour')
