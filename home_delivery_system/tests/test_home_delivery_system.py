# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHomeDeliverySystem(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Customer',
        })
        # Delivery Employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Delivery Boy',
        })
        # Product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100,
        })
        # Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'price_unit': 100,
                'name': 'Test Product',
            })]
        })
        cls.sale_order.action_confirm()
        # Delivery Order
        cls.picking = cls.sale_order.picking_ids[:1]

    def test_assign_delivery(self):
        """Test assigning delivery person."""
        self.picking.delivery_boy_id = self.employee.id
        self.picking.assign_delivery()
        self.assertEqual(
            self.picking.delivery_state,
            'assigned'
        )
        self.assertTrue(
            self.picking.is_assign_visibility
        )

    def test_assign_delivery_without_person(self):
        """Test validation when delivery person missing."""
        with self.assertRaises(ValidationError):
            self.picking.assign_delivery()

    def test_reset_to_draft(self):
        """Test reset delivery values."""

        self.picking.write({
            'delivery_boy_id': self.employee.id,
            'delivery_state': 'assigned',
            'is_broadcast_order': True,
            'order_source': 'website',
            'delivery_assign_date': fields.Date.today(),
            'distance': 10,
            'payment_status': 'paid',
            'is_complete': True,
        })

        self.picking.reset_to_draft()

        self.assertEqual(
            self.picking.delivery_state,
            'draft'
        )

        self.assertFalse(
            self.picking.delivery_boy_id
        )

        self.assertFalse(
            self.picking.is_complete
        )

    # ---------------------------------------------------------
    # TEST: reschedule wizard
    # ---------------------------------------------------------

    def test_reschedule_delivery_person(self):
        """Test rescheduling delivery person."""

        new_employee = self.env['hr.employee'].create({
            'name': 'New Delivery Boy',
        })

        wizard = self.env[
            'delivery.person.reschedule'
        ].with_context({
            'params': {
                'id': self.picking.id
            }
        }).create({
            'delivery_boy_id': new_employee.id,
            'reschedule_reason': 'Delivery reassigned',
        })

        wizard.reschedule_action()

        self.assertEqual(
            self.picking.delivery_boy_id,
            new_employee
        )

        self.assertEqual(
            self.picking.reschedule_reason,
            'Delivery reassigned'
        )