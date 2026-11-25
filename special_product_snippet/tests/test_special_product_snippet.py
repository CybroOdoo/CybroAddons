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
import json
from unittest.mock import patch

from odoo.tests import common, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.special_product_snippet.controllers.special_product_snippet import SpecialProduct


@tagged('post_install', '-at_install')
class TestSpecialProductSnippetController(common.TransactionCase):
    """Unit tests for the SpecialProduct controller logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = SpecialProduct()
        cls.website = cls.env['website'].search([], limit=1)
        cls.product = cls.env['product.template'].create({
            'name': 'Test Special Gadget',
            'list_price': 149.99,
            'website_published': True,
        })

    def test_render_all_templates(self):
        """Verify that all 4 dynamic templates render valid HTML with correct product context."""
        templates = [
            'special_product_snippet.first_dynamic_template',
            'special_product_snippet.second_dynamic_template',
            'special_product_snippet.third_dynamic_template',
            'special_product_snippet.fourth_dynamic_template',
        ]
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            for tmpl in templates:
                res = self.controller.render_template(id=self.product.id, template=tmpl)
                self.assertIn('html', res, f"Expected 'html' key for template {tmpl}")
                self.assertIn(self.product.name, res['html'], f"Expected product name in HTML for {tmpl}")
                self.assertIn('qcontext', res)
                self.assertEqual(res['qcontext']['display_name'], self.product.display_name)
                self.assertEqual(res['qcontext']['list_price'], self.product.list_price)

    def test_render_fallback_template(self):
        """Verify invalid or empty template names safely fall back to the first dynamic template."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            # Non-existent template name
            res_invalid = self.controller.render_template(
                id=self.product.id, template='special_product_snippet.non_existent_template'
            )
            self.assertIn('html', res_invalid)
            self.assertIn(self.product.name, res_invalid['html'])
            self.assertIn('first-product-page', res_invalid['html'])

            # None template
            res_none = self.controller.render_template(id=self.product.id, template=None)
            self.assertIn('html', res_none)
            self.assertIn('first-product-page', res_none['html'])

            # Empty string template
            res_empty = self.controller.render_template(id=self.product.id, template='')
            self.assertIn('html', res_empty)
            self.assertIn('first-product-page', res_empty['html'])

    def test_render_params_json_string(self):
        """Verify backward-compatibility with JSON string parameters blob."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            params_str = json.dumps({
                'id': self.product.id,
                'template': 'special_product_snippet.second_dynamic_template',
            })
            res = self.controller.render_template(params=params_str)
            self.assertIn('html', res)
            self.assertIn(self.product.name, res['html'])
            self.assertIn('second-product-page', res['html'])

    def test_render_params_dict(self):
        """Verify passing parameters as a dictionary."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            params_dict = {
                'id': self.product.id,
                'template': 'special_product_snippet.third_dynamic_template',
            }
            res = self.controller.render_template(params=params_dict)
            self.assertIn('html', res)
            self.assertIn(self.product.name, res['html'])
            self.assertIn('third-product-page', res['html'])

    def test_render_missing_product(self):
        """Verify requesting a non-existent or zero ID cleanly renders the unavailable template."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            for missing_id in [0, 9999999, None]:
                res = self.controller.render_template(id=missing_id)
                self.assertEqual(res.get('error'), 'unavailable')
                self.assertIn('html', res)
                self.assertIn('no longer available', res['html'])

    def test_render_website_url_fallback(self):
        """Verify fallback shop link when product website_url is unset."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            # Create a mock or patch website_url return value
            with patch.object(type(self.product), 'website_url', new=property(lambda self: False)):
                res = self.controller.render_template(id=self.product.id)
                self.assertIn('html', res)
                self.assertEqual(res['qcontext']['website_url'], f'/shop/{self.product.id}')

    def test_render_without_request_website(self):
        """Verify currency and website resolution when request.website is not pre-set."""
        with MockRequest(self.env):
            # MockRequest without explicit website falls back to database website
            res = self.controller.render_template(id=self.product.id)
            self.assertIn('html', res)
            self.assertIn(self.product.name, res['html'])

    def test_render_fallback_global_website(self):
        """Verify fallback to global website when no website matches company_id."""
        with MockRequest(self.env):
            orig_search = self.env['website'].search
            def search_side_effect(domain, *args, **kwargs):
                if domain and ('company_id', '=', self.env.company.id) in domain:
                    return self.env['website']
                return orig_search(domain, *args, **kwargs)

            with patch.object(type(self.env['website']), 'search', side_effect=search_side_effect):
                res = self.controller.render_template(id=self.product.id)
                self.assertIn('html', res)
                self.assertIn(self.product.name, res['html'])

    def test_render_exception_handling(self):
        """Verify that QWeb rendering failures are caught and return user-friendly alert HTML."""
        with MockRequest(self.env, website=self.website) as req:
            req.website = self.website
            with patch.object(type(self.env['ir.qweb']), '_render', side_effect=Exception("Simulated render crash")):
                res = self.controller.render_template(id=self.product.id)
                self.assertIn('error', res)
                self.assertEqual(res['error'], "Simulated render crash")
                self.assertIn('alert alert-danger', res['html'])
                self.assertIn("Failed to load product", res['html'])


@tagged('post_install', '-at_install')
class TestSpecialProductSnippetHttp(common.HttpCase):
    """End-to-end HTTP integration tests for the /website/snippet/special/render route."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'HTTP Test Snippet Item',
            'list_price': 89.0,
            'website_published': True,
        })
        cls.env.flush_all()

    def test_http_jsonrpc_render(self):
        """Test public JSON-RPC endpoint request."""
        res = self.url_open(
            '/website/snippet/special/render',
            json={
                'params': {
                    'id': self.product.id,
                    'template': 'special_product_snippet.fourth_dynamic_template',
                }
            },
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('result', data)
        result = data['result']
        self.assertIn('html', result)
        self.assertIn(self.product.name, result['html'])
        self.assertIn('product-card-page', result['html'])

    def test_http_jsonrpc_missing_product(self):
        """Test public JSON-RPC request for missing product returns unavailable message."""
        res = self.url_open(
            '/website/snippet/special/render',
            json={'params': {'id': 999999}},
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('result', data)
        result = data['result']
        self.assertEqual(result.get('error'), 'unavailable')
        self.assertIn('no longer available', result['html'])
