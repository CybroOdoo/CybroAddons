# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestTenderSales(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.TenderType = cls.env['sale.tender.type']
        cls.Tender = cls.env['sale.tender']
        cls.TenderLine = cls.env['sale.tender.line']
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderGroup = cls.env['sale.order.group']
        cls.SaleOrderLine = cls.env['sale.order.line']

        cls.partner1 = cls.env['res.partner'].create({
            'name': 'Vendor 1'
        })

        cls.partner2 = cls.env['res.partner'].create({
            'name': 'Vendor 2'
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Laptop',
            'list_price': 1000.0,
            'type': 'consu',
        })

        cls.tender_type = cls.TenderType.search([], limit=1)

        if not cls.tender_type:
            cls.tender_type = cls.TenderType.create({
                'name': 'Test Tender Type',
            })

    # -------------------------------------------------------------------------
    # Tender Flow
    # -------------------------------------------------------------------------

    def test_tender_flow_and_states(self):
        """Test tender workflow states."""

        tender = self.Tender.create({
            'type_id': self.tender_type.id,
        })

        self.assertEqual(tender.state, 'draft')

        line = self.TenderLine.create({
            'tender_id': tender.id,
            'product_id': self.product.id,
            'product_qty': 5,
        })

        line._onchange_product_id()

        self.assertEqual(line.price_unit, 1000.0)

        tender.action_in_progress()
        self.assertEqual(tender.state, 'in_progress')

        tender.action_open()
        self.assertEqual(tender.state, 'open')

        tender.action_done()
        self.assertEqual(tender.state, 'done')

        tender.action_reset_to_draft()
        self.assertEqual(tender.state, 'draft')

        tender.action_cancel()
        self.assertEqual(tender.state, 'cancel')

    # -------------------------------------------------------------------------
    # Tender + Sale Order
    # -------------------------------------------------------------------------

    def test_sale_order_tender_link(self):
        """Test tender linked with sale order."""

        tender = self.Tender.create({
            'type_id': self.tender_type.id,
        })

        tender_line = self.TenderLine.create({
            'tender_id': tender.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 1000,
        })

        so = self.SaleOrder.create({
            'partner_id': self.partner1.id,
            'tender_id': tender.id,
        })

        # manually create SO line because onchange
        # won't persist automatically in tests
        so_line = self.SaleOrderLine.create({
            'order_id': so.id,
            'product_id': tender_line.product_id.id,
            'product_uom_qty': tender_line.product_qty,
            'price_unit': tender_line.price_unit,
            'name': tender_line.product_id.name,
        })

        self.assertEqual(len(so.order_line), 1)
        self.assertEqual(so_line.product_uom_qty, 10)

    # -------------------------------------------------------------------------
    # Alternative Comparison
    # -------------------------------------------------------------------------

    def test_alternative_comparison(self):
        """Test alternative order comparison."""

        so_group = self.SaleOrderGroup.create({})

        so1 = self.SaleOrder.create({
            'partner_id': self.partner1.id,
            'sale_group_id': so_group.id,
        })

        self.SaleOrderLine.create({
            'order_id': so1.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 1000,
            'name': self.product.name,
        })

        so2 = self.SaleOrder.create({
            'partner_id': self.partner2.id,
            'sale_group_id': so_group.id,
        })

        self.SaleOrderLine.create({
            'order_id': so2.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 900,
            'name': self.product.name,
        })

        compare_action = so1.action_compare_alternative_lines()

        self.assertEqual(
            compare_action['res_model'],
            'sale.order.line'
        )

    # -------------------------------------------------------------------------
    # Choose Action
    # -------------------------------------------------------------------------

    def test_action_choose_and_clear_quantities(self):
        """Test choosing one quotation line."""

        so_group = self.SaleOrderGroup.create({})

        so1 = self.SaleOrder.create({
            'partner_id': self.partner1.id,
            'sale_group_id': so_group.id,
        })

        so1_line = self.SaleOrderLine.create({
            'order_id': so1.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 1000,
            'name': self.product.name,
        })

        so2 = self.SaleOrder.create({
            'partner_id': self.partner2.id,
            'sale_group_id': so_group.id,
        })

        so2_line = self.SaleOrderLine.create({
            'order_id': so2.id,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'price_unit': 1200,
            'name': self.product.name,
        })

        so1_line.action_choose()

        self.assertEqual(so1_line.product_uom_qty, 2.0)
        self.assertEqual(so2_line.product_uom_qty, 0.0)

    # -------------------------------------------------------------------------
    # Best Tender Lines
    # -------------------------------------------------------------------------

    def test_get_tender_best_lines(self):
        """Test best line calculation."""

        so_group = self.SaleOrderGroup.create({})

        so1 = self.SaleOrder.create({
            'partner_id': self.partner1.id,
            'sale_group_id': so_group.id,
        })

        so1_line = self.SaleOrderLine.create({
            'order_id': so1.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 1000,
            'name': self.product.name,
        })

        so2 = self.SaleOrder.create({
            'partner_id': self.partner2.id,
            'sale_group_id': so_group.id,
        })

        so2_line = self.SaleOrderLine.create({
            'order_id': so2.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 800,
            'name': self.product.name,
        })

        best_lines = so1.get_tender_best_lines()

        self.assertTrue(best_lines)
        self.assertIn(so1_line.id, best_lines[0])