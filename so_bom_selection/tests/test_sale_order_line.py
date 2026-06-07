# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import common

class TestSaleOrderLine(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderLine, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'bom_id': self.bom.id,
            })],
        })

    def test_bom_and_template_fields(self):
        line = self.sale_order.order_line
        self.assertEqual(line.bom_id, self.bom, "BOM should be correctly set on the line")
        self.assertEqual(line.product_template_id, self.product.product_tmpl_id, "Product template should match the product")

    def test_action_launch_stock_rule(self):
        self.sale_order.action_confirm()
        mo = self.env['mrp.production'].search([('sale_line_id', '=', self.sale_order.order_line.id)])
        moves = self.env['stock.move'].search([('sale_line_id', '=', self.sale_order.order_line.id)])
        for move in moves:
            self.assertEqual(move.created_production_id.id, mo.id, "Stock move should be linked to the created MO")
