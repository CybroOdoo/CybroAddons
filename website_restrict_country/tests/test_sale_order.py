# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls._get_country('US', 'United States')
        cls.country_ca = cls._get_country('CA', 'Canada')
        cls.country_mx = cls._get_country('MX', 'Mexico')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website Restrict Country Partner',
        })

    @classmethod
    def _get_country(cls, code, name):
        country = cls.env['res.country'].search([('code', '=', code)], limit=1)
        if not country:
            country = cls.env['res.country'].create({
                'name': name,
                'code': code,
            })
        return country

    @classmethod
    def _create_product(cls, name, countries=None):
        values = {
            'name': name,
            'sale_ok': True,
            'website_published': True,
        }
        if countries:
            values.update({
                'country_availability': 'selected',
                'country_selection_ids': [
                    (0, 0, {'country_id': country.id}) for country in countries
                ],
            })
        return cls.env['product.product'].create(values)

    def _create_sale_order(self, products):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1.0,
                }) for product in products
            ],
        })

    def test_common_country_list_returns_empty_for_all_country_products(self):
        product = self._create_product('Unrestricted Product')
        sale_order = self._create_sale_order(product)

        self.assertEqual(sale_order.get_common_country_list, [])

    def test_common_country_list_returns_selected_product_countries(self):
        product = self._create_product(
            'US and CA Product',
            countries=self.country_us | self.country_ca,
        )
        sale_order = self._create_sale_order(product)

        self.assertEqual(
            set(sale_order.get_common_country_list),
            {self.country_us.id, self.country_ca.id},
        )

    def test_common_country_list_returns_intersection_for_multiple_products(self):
        first_product = self._create_product(
            'US and CA Product',
            countries=self.country_us | self.country_ca,
        )
        second_product = self._create_product(
            'CA and MX Product',
            countries=self.country_ca | self.country_mx,
        )
        sale_order = self._create_sale_order(first_product | second_product)

        self.assertEqual(sale_order.get_common_country_list, [self.country_ca.id])

    def test_common_country_list_ignores_all_country_products(self):
        unrestricted_product = self._create_product('Unrestricted Product')
        restricted_product = self._create_product(
            'US Restricted Product',
            countries=self.country_us,
        )
        sale_order = self._create_sale_order(unrestricted_product | restricted_product)

        self.assertEqual(sale_order.get_common_country_list, [self.country_us.id])
