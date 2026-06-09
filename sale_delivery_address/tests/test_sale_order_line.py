# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSaleOrderLine(TransactionCase):
    """Test cases for the SaleOrderLine model (sale.order.line extension)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a partner to use as customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer Test',
        })

        # Create a service product
        cls.service_product = cls.env['product.product'].create({
            'name': 'Consulting Service',
            'type': 'service',
        })

        # Create a consumable/storable product
        cls.consumable_product = cls.env['product.product'].create({
            'name': 'Physical Table',
            'type': 'consu',
        })

        # Create a Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_is_address_readonly_for_service(self):
        """Test that is_address_readonly is True for service products."""
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.service_product.id,
            'product_uom_qty': 1.0,
        })
        self.assertTrue(
            line.is_address_readonly,
            "is_address_readonly should be True for a service product."
        )

    def test_is_address_readonly_for_consumable(self):
        """Test that is_address_readonly is False for consumable/storable products."""
        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.consumable_product.id,
            'product_uom_qty': 1.0,
        })
        self.assertFalse(
            line.is_address_readonly,
            "is_address_readonly should be False for a consumable product."
        )
