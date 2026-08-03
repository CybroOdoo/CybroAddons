# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
################################################################################
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestFreightOrder(common.TransactionCase):

    def setUp(self):
        super(TestFreightOrder, self).setUp()
        self.partner_shipper = self.env['res.partner'].create({'name': 'Test Shipper', 'email': 'shipper@test.com'})
        self.partner_agent = self.env['res.partner'].create({'name': 'Test Agent', 'email': 'agent@test.com'})
        
        self.port_loading = self.env['freight.port'].create({
            'name': 'Loading Port',
            'country_id': self.env.ref('base.us').id,
            'water': True
        })
        self.port_discharging = self.env['freight.port'].create({
            'name': 'Discharging Port',
            'country_id': self.env.ref('base.be').id,
            'water': True
        })

        self.container = self.env['freight.container'].create({
            'name': 'Test Container',
            'size': 20,
            'weight': 1000,
            'volume': 500,
        })

        self.pricing = self.env['freight.price'].create({
            'name': 'Standard Pricing',
            'weight': 10,
            'volume': 20
        })

    def test_01_freight_order_flow(self):
        """Test the basic flow of a freight order"""
        # Create Freight Order
        order = self.env['freight.order'].create({
            'shipper_id': self.partner_shipper.id,
            'type': 'export',
            'transport_type': 'water',
            'loading_port_id': self.port_loading.id,
            'discharging_port_id': self.port_discharging.id,
            'agent_id': self.partner_agent.id,
        })
        self.assertEqual(order.state, 'draft', "Order should be in draft state")

        # Add Order Line
        line = self.env['freight.order.line'].create({
            'order_id': order.id,
            'container_id': self.container.id,
            'billing_type': 'weight',
            'pricing_id': self.pricing.id,
            'weight': 100,
        })
        line._onchange_price()
        self.assertEqual(line.price, 10, "Unit price should be 10 based on pricing")
        line._onchange_total_price()
        self.assertEqual(line.total_price, 1000, "Total price should be 1000")

        order._compute_total_order_price()
        self.assertEqual(order.total_order_price, 1000, "Order total price should be 1000")

        # Submit Order
        order.action_submit()
        self.assertEqual(order.state, 'submit', "Order should be in submit state")

        # Create Custom Clearance
        order.action_create_custom_clearance()
        self.assertTrue(order.clearance, "Clearance should be True")
        clearance = self.env['custom.clearance'].search([('freight_id', '=', order.id)])
        self.assertTrue(clearance, "Custom clearance should be created")
        
        # Try to confirm without confirming clearance (should fail)
        with self.assertRaises(ValidationError):
            order.action_confirm()

        # Confirm Clearance
        clearance.action_confirm()
        self.assertEqual(clearance.state, 'confirm', "Clearance should be confirmed")

        # Confirm Order
        order.action_confirm()
        self.assertEqual(order.state, 'confirm', "Order should be confirmed")
        self.assertEqual(self.container.state, 'reserve', "Container should be reserved")

        # Create Invoice
        order.action_create_invoice()
        self.assertEqual(order.state, 'invoice', "Order should be in invoice state")
        invoice = self.env['account.move'].search([('ref', '=', order.name)])
        self.assertTrue(invoice, "Invoice should be created")

        # Done Order
        order.action_done()
        self.assertEqual(order.state, 'done', "Order should be done")
        self.assertEqual(self.container.state, 'available', "Container should be available again")

    def test_02_order_line_constraints(self):
        """Test weight and volume constraints on order lines"""
        order = self.env['freight.order'].create({
            'shipper_id': self.partner_shipper.id,
            'type': 'export',
            'transport_type': 'water',
            'loading_port_id': self.port_loading.id,
            'discharging_port_id': self.port_discharging.id,
            'agent_id': self.partner_agent.id,
        })

        # Test weight constraint
        with self.assertRaises(ValidationError):
            self.env['freight.order.line'].create({
                'order_id': order.id,
                'container_id': self.container.id,
                'billing_type': 'weight',
                'weight': 2000, # Max capacity is 1000
            })

        # Test volume constraint
        with self.assertRaises(ValidationError):
            self.env['freight.order.line'].create({
                'order_id': order.id,
                'container_id': self.container.id,
                'billing_type': 'volume',
                'volume': 600, # Max capacity is 500
            })
