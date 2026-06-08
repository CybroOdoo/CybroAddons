# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Technologies (odoo@cybrosys.com)
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

from types import SimpleNamespace
from unittest.mock import patch

from odoo.fields import Date

from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon
from odoo.addons.delivery_slot.controllers.delivery_slot import Cart


class TestDeliverySlotController(WebsiteSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = Cart()
        cls.home_slot = cls.env['slot.time'].create({
            'name': 'Controller Home Slot',
            'slot_type': 'home',
            'time_from': '7',
            'time_to': '9',
        })
        cls.office_slot = cls.env['slot.time'].create({
            'name': 'Controller Office Slot',
            'slot_type': 'office',
            'time_from': '11',
            'time_to': '13',
        })

    def test_cart_adds_delivery_slot_values_to_qcontext(self):
        response = SimpleNamespace(qcontext={})

        with (
            MockRequest(self.env, website=self.website),
            patch.object(PaymentPortal, 'cart', return_value=response, create=True),
        ):
            result = Cart.cart.original_endpoint(self.controller)

        self.assertIs(result, response)
        self.assertIn('is_delivery_slot', response.qcontext)
        self.assertIn(self.home_slot, response.qcontext['slots'])
        self.assertIn(self.home_slot, response.qcontext['slot_home'])
        self.assertNotIn(self.home_slot, response.qcontext['slot_office'])

    def test_update_cart_adds_delivery_slot_values_to_response(self):
        response = {}

        with (
            MockRequest(self.env, website=self.website),
            patch.object(PaymentPortal, 'update_cart', return_value=response, create=True),
        ):
            result = self.controller.update_cart()

        self.assertIs(result, response)
        self.assertIn('is_delivery_slot', response)
        self.assertIn(self.office_slot, response['slots'])
        self.assertIn(self.office_slot, response['slot_office'])
        self.assertNotIn(self.office_slot, response['slot_home'])

    def test_get_option_returns_slots_for_selected_type(self):
        with MockRequest(self.env, website=self.website):
            options = self.controller.get_option(selected_option='home')

        self.assertIn([self.home_slot.id, self.home_slot.name], options)
        self.assertNotIn([self.office_slot.id, self.office_slot.name], options)

    def test_set_delivery_date_updates_matching_cart_line(self):
        line = self.cart.order_line[:1]
        delivery_date = Date.to_date('2026-06-17')

        with MockRequest(self.env, website=self.website, sale_order_id=self.cart.id):
            result = self.controller.set_delivery_date(
                line_id=line.id,
                delivery_date=delivery_date,
            )

        self.assertEqual(result, {'success': 'Delivery date updated.'})
        self.assertEqual(line.delivery_date, delivery_date)

    def test_set_delivery_slot_requires_delivery_date(self):
        line = self.cart.order_line[:1]
        line.delivery_date = False

        with MockRequest(self.env, website=self.website, sale_order_id=self.cart.id):
            result = self.controller.set_delivery_slot(
                line_id=line.id,
                delivery_slot=self.home_slot.id,
            )

        self.assertEqual(result['error_type'], 'missing_date')
        self.assertFalse(line.slot_id)

    def test_set_delivery_slot_rejects_full_slot(self):
        line = self.cart.order_line[:1]
        line.delivery_date = Date.to_date('2026-06-18')
        self.env['delivery.slot'].create({
            'delivery_date': line.delivery_date,
            'slot_id': self.home_slot.id,
            'delivery_limit': 0,
        })

        with MockRequest(self.env, website=self.website, sale_order_id=self.cart.id):
            result = self.controller.set_delivery_slot(
                line_id=line.id,
                delivery_slot=self.home_slot.id,
            )

        self.assertEqual(result['error_type'], 'limit_reached')
        self.assertFalse(line.slot_id)

    def test_set_delivery_slot_updates_matching_cart_line(self):
        line = self.cart.order_line[:1]
        line.delivery_date = Date.to_date('2026-06-19')

        with MockRequest(self.env, website=self.website, sale_order_id=self.cart.id):
            result = self.controller.set_delivery_slot(
                line_id=line.id,
                delivery_slot=self.office_slot.id,
            )

        self.assertEqual(result, {'success': 'Delivery slot updated.'})
        self.assertEqual(line.slot_id, self.office_slot)
