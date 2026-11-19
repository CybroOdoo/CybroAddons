# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import re

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged('post_install', '-at_install')
class TestWarrantyClaimController(HttpCaseWithUserPortal):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warranty_product = cls.env['product.product'].create({
            'name': 'Controller Warranty Product',
            'is_warranty_available': True,
            'warranty_duration': 24,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Controller Non Warranty Product',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_portal.id,
            'order_line': [
                Command.create({'product_id': cls.warranty_product.id}),
                Command.create({'product_id': cls.other_product.id}),
            ],
        })
        cls.sale_order.action_confirm()
        other_customer = cls.env['res.partner'].create({
            'name': 'Other Warranty Customer'})
        cls.other_order = cls.env['sale.order'].create({
            'partner_id': other_customer.id,
            'order_line': [
                Command.create({'product_id': cls.warranty_product.id}),
            ],
        })
        cls.other_order.action_confirm()

    def _post_claim(self, sale_order_id, product_id):
        page = self.url_open('/warranty')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        return self.url_open('/warranty/claim/submit', data={
            'csrf_token': token.group(1),
            'sale_order_id': sale_order_id,
            'product_id': product_id,
            'description': 'Stopped working',
        })

    def _submit_claim(self, order, product):
        return self._post_claim(order.id, product.id)

    def _claims(self):
        return self.env['warranty.claim'].search([
            ('customer_id', '=', self.partner_portal.id)])

    def test_warranty_page_requires_login(self):
        response = self.url_open('/warranty', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))

    def test_warranty_page_lists_own_orders_only(self):
        self.authenticate('portal', 'portal')

        response = self.url_open('/warranty')

        self.assertIn(self.sale_order.name, response.text)
        self.assertNotIn(self.other_order.name, response.text)

    def test_warranty_products_of_own_order(self):
        self.authenticate('portal', 'portal')

        products = self.make_jsonrpc_request(
            '/warranty/products', {'order_id': self.sale_order.id})
        other_products = self.make_jsonrpc_request(
            '/warranty/products', {'order_id': self.other_order.id})

        self.assertEqual([p['id'] for p in products],
                         [self.warranty_product.id])
        self.assertEqual(other_products, [])

    def test_submit_claim(self):
        self.authenticate('portal', 'portal')

        response = self._submit_claim(self.sale_order, self.warranty_product)

        self.assertIn('submitted successfully', response.text)
        claim = self._claims()
        self.assertEqual(claim.sale_order_id, self.sale_order)
        self.assertEqual(claim.product_id, self.warranty_product)
        self.assertEqual(claim.description, 'Stopped working')

        response = self._submit_claim(self.sale_order, self.warranty_product)
        self.assertIn('already exists', response.text)
        self.assertEqual(len(self._claims()), 1)

    def test_submit_claim_rejects_invalid_values(self):
        self.authenticate('portal', 'portal')

        self._submit_claim(self.sale_order, self.other_product)
        self._submit_claim(self.other_order, self.warranty_product)
        response = self._post_claim('abc', 'xyz')

        self.assertIn('Select a sale order and a product', response.text)
        self.assertFalse(self._claims())

    def test_submit_claim_after_rejection(self):
        self.authenticate('portal', 'portal')
        self._submit_claim(self.sale_order, self.warranty_product)
        self._claims().change_status_rejected()

        response = self._submit_claim(self.sale_order, self.warranty_product)

        self.assertIn('submitted successfully', response.text)
        self.assertEqual(self._claims().mapped('state'),
                         ['draft', 'rejected'])

    def test_portal_claims(self):
        self.env['warranty.claim'].create({
            'customer_id': self.partner_portal.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.warranty_product.id,
        })
        self.authenticate('portal', 'portal')

        counters = self.make_jsonrpc_request('/my/counters', {'counters': {
            'claim_count': 'client_category',
            'order_count': 'client_category',
        }})
        response = self.url_open('/my/claims')

        self.assertEqual(counters['claim_count'], 1)
        self.assertEqual(counters['order_count'], 1)
        self.assertIn(self.sale_order.name, response.text)
        self.assertIn(self.warranty_product.name, response.text)
        self.assertIn('Draft', response.text)
