# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies @cybrosys(odoo@cybrosys.com)
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
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAutomaticInvoiceAndPost(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.customer = cls.env['res.partner'].create({
            'name': 'Invoice Customer',
            'email': 'customer@example.com',
        })
        cls.product_uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.product'].create({
            'name': 'Deliverable Product',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100.0,
            'uom_id': cls.product_uom_unit.id,
            'uom_po_id': cls.product_uom_unit.id,
        })

    def _prepare_sale_order_with_delivery(self):
        print("1111111111")
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product_uom_unit.id,
            'price_unit': 100.0,
        })
        sale_order.action_confirm()
        picking = sale_order.picking_ids[:1]
        picking.move_ids.quantity_done = 1.0
        return sale_order, picking

    def test_validate_delivery_creates_and_posts_invoice(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_invoice_and_post.is_create_invoice_delivery_validate',
            '1',
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_invoice_and_post.is_auto_send_invoice',
            '0',
        )

        sale_order, picking = self._prepare_sale_order_with_delivery()
        picking.button_validate()

        self.assertTrue(sale_order.invoice_ids, 'Invoice should be created')
        self.assertEqual(
            sale_order.invoice_ids.mapped('state'),
            ['posted'],
            'Invoice should be posted automatically',
        )
