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
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common_setup_methods import setup_product_combo_items
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged('post_install', '-at_install')
class TestPosDeleteOrderLine(TestPointOfSaleHttpCommon):
    """Test removing order lines from the POS cart."""

    def test_01_delete_orderline_and_clear_all(self):
        """Exercise regular-line, combo-line, cancel, and clear-all actions."""
        setup_product_combo_items(self)
        self.env["product.product"].create(
            {
                "name": "Delete Test Combo",
                "available_in_pos": True,
                "list_price": 20,
                "type": "combo",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "combo_ids": [(6, 0, [self.desk_accessories_combo.id])],
            }
        )
        self.start_pos_tour('pos_delete_orderline_tour')
