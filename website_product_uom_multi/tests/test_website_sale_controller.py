# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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
import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.website_product_uom_multi.controllers import (
    website_sale as website_sale_controller_module,
)


class FakeRequest:

    def __init__(self, env, website=None):
        self.env = env
        self.website = website
        self.session = {}


class FakeWebsite:

    def __init__(self, order):
        self.order = order
        self.reset_count = 0

    def sale_get_order(self, force_create=False):
        return self.order

    def sale_reset(self):
        self.reset_count += 1

    def with_context(self, **kwargs):
        return self


@tagged('post_install', '-at_install')
class TestWebsiteSaleController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website UoM Controller Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Website UoM Controller Product',
            'type': 'consu',
            'list_price': 10.0,
            'uom_id': cls.uom_unit.id,
        })

    def _create_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.env['website'].get_current_website().id,
        })

    def test_cart_update_json_adds_line_with_selected_uom(self):
        controller = website_sale_controller_module.WebsiteProductUom()
        order = self._create_order()
        fake_request = FakeRequest(self.env, FakeWebsite(order))

        with patch.object(website_sale_controller_module, 'request', fake_request):
            with patch.object(
                controller, '_get_cart_notification_information', return_value={}
            ):
                result = type(controller).cart_update_json.__wrapped__(
                    controller,
                    product_id=self.product.id,
                    add_qty=2,
                    display=False,
                    uom_id=str(self.uom_pack_6.id),
                )

        line = self.env['sale.order.line'].browse(result['line_id'])
        self.assertEqual(line.product_uom_id, self.uom_pack_6)
        self.assertEqual(result['cart_quantity'], 2)
        self.assertEqual(fake_request.session['website_sale_cart_quantity'], 2)

    def test_cart_options_update_json_adds_main_product_with_selected_uom(self):
        controller = website_sale_controller_module.WebsiteProductUom.WebsiteProductVariant()
        order = self._create_order()
        fake_request = FakeRequest(self.env, FakeWebsite(order))
        product_and_options = json.dumps([{
            'product_id': self.product.id,
            'product_template_id': self.product.product_tmpl_id.id,
            'quantity': 3,
            'unique_id': 'main-product',
            'parent_unique_id': False,
            'product_custom_attribute_values': False,
            'no_variant_attribute_values': False,
            'uom_id': str(self.uom_pack_6.id),
        }])

        with patch.object(website_sale_controller_module, 'request', fake_request):
            with patch.object(
                controller, '_get_cart_notification_information', return_value={}
            ):
                result = type(controller).cart_options_update_json.__wrapped__(
                    controller,
                    product_and_options=product_and_options,
                )

        line = self.env['sale.order.line'].browse(result['line_id'])
        self.assertEqual(line.product_uom_id, self.uom_pack_6)
        self.assertEqual(result['cart_quantity'], 3)
        self.assertEqual(fake_request.session['website_sale_cart_quantity'], 3)
