# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestWebsiteRestrictCountry(TransactionCase):

    def setUp(self):
        super().setUp()
        self.india = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        self.usa = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        self.france = self.env['res.country'].search([('code', '=', 'FR')], limit=1)

        self.website = self.env['website'].search([], limit=1)
        if not self.website:
            self.website = self.env['website'].create({
                'name': 'Test Website',
                'country_ids': [(6, 0, [self.india.id, self.usa.id, self.france.id])],
                'default_country_id': self.india.id,
                'cart_message': 'This product is not available in your country.',
            })
        else:
            self.website.write({
                'country_ids': [(6, 0, [self.india.id, self.usa.id, self.france.id])],
                'default_country_id': self.india.id,
                'cart_message': 'This product is not available in your country.',
            })

        self.product_all = self.env['product.template'].create({
            'name': 'Global Product',
            'type': 'consu',
            'country_availability': 'all',
            'list_price': 100.0,
        })

        self.product_restricted = self.env['product.template'].create({
            'name': 'Restricted Product',
            'type': 'consu',
            'country_availability': 'selected',
            'list_price': 200.0,
        })

        self.env['country.details'].create({
            'country_id': self.india.id,
            'product_tmpl_id': self.product_restricted.id,
        })
        self.env['country.details'].create({
            'country_id': self.usa.id,
            'product_tmpl_id': self.product_restricted.id,
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'country_id': self.india.id,
        })

        self.pricelist = self.env['product.pricelist'].search([], limit=1)

    def test_country_details_creation(self):
        country_detail = self.env['country.details'].create({
            'country_id': self.france.id,
            'product_tmpl_id': self.product_restricted.id,
        })
        self.assertEqual(country_detail.country_id, self.france)
        self.assertEqual(country_detail.country_code, self.france.code)
        self.assertEqual(country_detail.product_tmpl_id, self.product_restricted)

    def test_country_code_related_field(self):
        detail = self.env['country.details'].create({
            'country_id': self.india.id,
            'product_tmpl_id': self.product_restricted.id,
        })
        self.assertEqual(detail.country_code, 'IN')

    def test_product_template_default_availability(self):
        self.assertEqual(self.product_all.country_availability, 'all')

    def test_product_template_selected_availability(self):
        self.assertEqual(self.product_restricted.country_availability, 'selected')

    def test_product_country_selection_ids_populated(self):
        self.assertTrue(len(self.product_restricted.country_selection_ids) >= 2)
        country_ids = self.product_restricted.country_selection_ids.mapped('country_id')
        self.assertIn(self.india, country_ids)
        self.assertIn(self.usa, country_ids)

    def test_product_all_has_no_country_restrictions(self):
        self.assertEqual(self.product_all.country_availability, 'all')
        self.assertFalse(self.product_restricted.country_selection_ids.filtered(
            lambda r: r.product_tmpl_id == self.product_all))

    def test_website_country_ids(self):
        self.assertIn(self.india, self.website.country_ids)
        self.assertIn(self.usa, self.website.country_ids)
        self.assertIn(self.france, self.website.country_ids)

    def test_website_default_country(self):
        self.assertEqual(self.website.default_country_id, self.india)

    def test_website_cart_message(self):
        self.assertEqual(
            self.website.cart_message,
            'This product is not available in your country.'
        )

    def test_website_update_default_country(self):
        self.website.default_country_id = self.usa.id
        self.assertEqual(self.website.default_country_id, self.usa)

    def test_website_update_cart_message(self):
        new_msg = 'Sorry, this item cannot be shipped to your location.'
        self.website.cart_message = new_msg
        self.assertEqual(self.website.cart_message, new_msg)

    def _create_sale_order_with_products(self, product_templates):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        for tmpl in product_templates:
            product = tmpl.product_variant_ids[:1]
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': tmpl.list_price,
            })
        return order

    def test_get_common_country_list_all_products(self):
        order = self._create_sale_order_with_products([self.product_all])
        result = order.get_common_country_list
        self.assertEqual(result, [])

    def test_get_common_country_list_restricted_product(self):
        order = self._create_sale_order_with_products([self.product_restricted])
        result = order.get_common_country_list
        self.assertIn(self.india.id, result)
        self.assertIn(self.usa.id, result)

    def test_get_common_country_list_intersection(self):
        product_india_only = self.env['product.template'].create({
            'name': 'India Only Product',
            'type': 'consu',
            'country_availability': 'selected',
            'list_price': 150.0,
        })
        self.env['country.details'].create({
            'country_id': self.india.id,
            'product_tmpl_id': product_india_only.id,
        })
        order = self._create_sale_order_with_products(
            [self.product_restricted, product_india_only])
        result = order.get_common_country_list
        self.assertIn(self.india.id, result)
        self.assertNotIn(self.usa.id, result)

    def test_get_common_country_list_no_intersection(self):
        product_france_only = self.env['product.template'].create({
            'name': 'France Only Product',
            'type': 'consu',
            'country_availability': 'selected',
            'list_price': 180.0,
        })
        self.env['country.details'].create({
            'country_id': self.france.id,
            'product_tmpl_id': product_france_only.id,
        })
        product_india_only = self.env['product.template'].create({
            'name': 'India Only Product 2',
            'type': 'consu',
            'country_availability': 'selected',
            'list_price': 120.0,
        })
        self.env['country.details'].create({
            'country_id': self.india.id,
            'product_tmpl_id': product_india_only.id,
        })
        order = self._create_sale_order_with_products(
            [product_france_only, product_india_only])
        result = order.get_common_country_list
        self.assertEqual(result, [])

    def test_country_details_model_name(self):
        self.assertEqual(
            self.env['country.details']._description, 'Country Details')

    def test_product_availability_selection_values(self):
        field = self.env['product.template']._fields['country_availability']
        selection_keys = [k for k, _ in field.selection]
        self.assertIn('all', selection_keys)
        self.assertIn('selected', selection_keys)

    def test_multiple_country_details_per_product(self):
        self.env['country.details'].create({
            'country_id': self.france.id,
            'product_tmpl_id': self.product_restricted.id,
        })
        count = self.env['country.details'].search_count([
            ('product_tmpl_id', '=', self.product_restricted.id)
        ])
        self.assertGreaterEqual(count, 3)

    def test_website_remove_country_from_list(self):
        remaining = self.india | self.usa
        self.website.country_ids = [(6, 0, remaining.ids)]
        self.assertNotIn(self.france, self.website.country_ids)
        self.assertIn(self.india, self.website.country_ids)
