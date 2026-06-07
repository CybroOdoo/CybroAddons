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

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_partner = cls.env['res.partner'].create({
            'name': 'Agent Partner',
            'email': 'agent.partner@example.com',
            'is_agent': True,
        })
        cls.customer_partner = cls.env['res.partner'].create({
            'name': 'Customer Partner',
            'email': 'customer.partner@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Shopping Through Agent Product',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 150.0,
            'sale_ok': True,
        })

    def test_prepare_invoice_propagates_agent_to_invoice_values(self):
        order = self.env['sale.order'].create({
            'partner_id': self.customer_partner.id,
            'partner_invoice_id': self.customer_partner.id,
            'partner_shipping_id': self.customer_partner.id,
            'agent_id': self.agent_partner.id,
            'order_line': [
                Command.create({
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.product.list_price,
                }),
            ],
        })

        invoice_vals = order._prepare_invoice()

        self.assertEqual(invoice_vals['agent_id'], self.agent_partner.id)

    def test_create_invoice_keeps_agent_link(self):
        order = self.env['sale.order'].create({
            'partner_id': self.customer_partner.id,
            'partner_invoice_id': self.customer_partner.id,
            'partner_shipping_id': self.customer_partner.id,
            'agent_id': self.agent_partner.id,
            'order_line': [
                Command.create({
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.product.list_price,
                }),
            ],
        })

        order.action_confirm()
        invoice = order._create_invoices()

        self.assertEqual(invoice.agent_id, self.agent_partner)
