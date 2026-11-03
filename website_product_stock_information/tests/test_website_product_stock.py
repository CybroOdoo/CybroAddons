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
from odoo.addons.website_product_stock_information.controllers.website_sale import WebsiteSale
from odoo.addons.website_sale.tests.common import MockRequest
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestWebsiteProductStock(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')

        # Link website, company, and pricelist with a valid currency
        self.website = self.env.ref('website.default_website', raise_if_not_found=False) or self.env['website'].search([], limit=1)
        if not self.website:
            self.website = self.env['website'].create({
                'name': 'Test Website',
                'company_id': self.env.company.id,
            })
        if not self.website.company_id:
            self.website.company_id = self.env.company

        self.pricelist = self.website.pricelist_id or self.env['product.pricelist'].search([
            ('currency_id', '=', self.env.company.currency_id.id),
        ], limit=1)
        if not self.pricelist:
            self.pricelist = self.env['product.pricelist'].create({
                'name': 'Test Pricelist',
                'currency_id': self.env.company.currency_id.id,
                'company_id': self.env.company.id,
            })
        self.website.pricelist_id = self.pricelist

        self.product = self.env['product.product'].create({
            'name': 'Test Stock Product',
            'type': 'consu',
            'is_storable': True,
            'company_id': self.env.company.id,
        })
        self.template = self.product.product_tmpl_id.with_context(website_id=self.website.id)

        self.product2 = self.env['product.product'].create({
            'name': 'Test Stock Product 2',
            'type': 'consu',
            'is_storable': True,
            'company_id': self.env.company.id,
        })
        self.template2 = self.product2.product_tmpl_id.with_context(website_id=self.website.id)

        self.service_product = self.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
            'is_storable': False,
            'company_id': self.env.company.id,
        })

        self.env['ir.default'].sudo().search([
            ('field_id.model', '=', 'product.template'),
            ('field_id.name', 'in', ['location_type', 'stock_location_id', 'stock_type', 'show_availability', 'available_threshold']),
        ]).unlink()

    def _create_done_move(self, qty, src, dest, product=None):
        prod = product or self.product
        move = self.env['stock.move'].create({
            'product_id': prod.id,
            'product_uom_qty': qty,
            'uom_id': prod.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'company_id': self.env.company.id,
        })
        move.quantity = qty
        move._action_confirm()
        move._action_assign()
        move.picked = True
        move._action_done()
        return move

    def _create_confirmed_move(self, qty, src, dest, product=None):
        prod = product or self.product
        move = self.env['stock.move'].create({
            'product_id': prod.id,
            'product_uom_qty': qty,
            'uom_id': prod.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'company_id': self.env.company.id,
        })
        move._action_confirm()
        return move

    def test_01_selection_methods_and_multi_recordset(self):
        templates = self.template + self.template2
        options_loc = templates._get_location_type_selection()
        keys_loc = [k for k, _ in options_loc]
        self.assertIn('all', keys_loc)
        self.assertIn('specific', keys_loc)

        options_stock = templates._get_stock_type_selection()
        keys_stock = [k for k, _ in options_stock]
        self.assertIn('on_hand', keys_stock)
        self.assertIn('forecast', keys_stock)

    def test_02_field_defaults_and_multi_recordset_write(self):
        templates = self.template + self.template2
        templates.write({
            'location_type': 'specific',
            'stock_location_id': self.stock_location.id,
            'stock_type': 'forecast',
        })
        self.assertEqual(self.template.location_type, 'specific')
        self.assertEqual(self.template.stock_location_id, self.stock_location)
        self.assertEqual(self.template.stock_type, 'forecast')
        self.assertEqual(self.template2.location_type, 'specific')
        self.assertEqual(self.template2.stock_location_id, self.stock_location)
        self.assertEqual(self.template2.stock_type, 'forecast')

    def test_03_combination_info_all_locations_on_hand(self):
        self._create_done_move(8, self.customer_location, self.stock_location)
        self.template.write({'location_type': 'all', 'stock_type': 'on_hand'})
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertIn('free_qty', info)
            self.assertGreaterEqual(info['free_qty'], 8)
            self.assertEqual(info['stock'], 'in_stock')

    def test_04_combination_info_all_locations_forecast(self):
        self.template.write({'location_type': 'all', 'stock_type': 'forecast'})
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertIn('free_qty', info)
            self.assertEqual(info['free_qty'], self.template.virtual_available)

    def test_05_combination_info_specific_location_in_stock(self):
        self._create_done_move(10, self.customer_location, self.stock_location)
        self._create_done_move(3, self.stock_location, self.customer_location)
        self.template.write({
            'location_type': 'specific',
            'stock_location_id': self.stock_location.id,
            'stock_type': 'on_hand',
        })
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertEqual(info['free_qty'], 7)
            self.assertEqual(info['stock'], 'in_stock')

    def test_06_combination_info_specific_location_out_of_stock(self):
        self.template.write({
            'location_type': 'specific',
            'stock_location_id': self.stock_location.id,
            'stock_type': 'on_hand',
        })
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertLessEqual(info.get('free_qty', 0), 0)
            self.assertEqual(info['stock'], 'out_of_stock')

    def test_07_combination_info_specific_location_forecast(self):
        self._create_confirmed_move(6, self.customer_location, self.stock_location)
        self.template.write({
            'location_type': 'specific',
            'stock_location_id': self.stock_location.id,
            'stock_type': 'forecast',
        })
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertGreaterEqual(info['free_qty'], 6)
            self.assertEqual(info['stock'], 'in_stock')

    def test_08_combination_info_fallback_ir_default(self):
        self.template.write({
            'location_type': False,
            'stock_location_id': False,
            'stock_type': False,
        })
        self.env['ir.default'].set('product.template', 'location_type', 'specific')
        self.env['ir.default'].set('product.template', 'stock_location_id', self.stock_location.id)
        self.env['ir.default'].set('product.template', 'stock_type', 'on_hand')
        self.env['ir.default'].set('product.template', 'show_availability', True)
        self.env['ir.default'].set('product.template', 'available_threshold', 5.0)

        self._create_done_move(4, self.customer_location, self.stock_location)
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            info = self.template._get_combination_info()
            self.assertTrue(info.get('show_availability'))
            self.assertEqual(info.get('available_threshold'), 5.0)
            self.assertEqual(info['free_qty'], 4)
            self.assertEqual(info['stock'], 'in_stock')

    def test_09_res_config_settings_set_and_get_values(self):
        settings = self.env['res.config.settings'].create({
            'location_type': 'specific',
            'stock_location_id': self.stock_location.id,
            'stock_type': 'forecast',
        })
        settings.set_values()

        stored_loc = self.env['ir.default']._get('product.template', 'location_type')
        self.assertEqual(stored_loc, 'specific')
        stored_loc_id = self.env['ir.default']._get('product.template', 'stock_location_id')
        self.assertEqual(stored_loc_id, self.stock_location.id)
        stored_stock_type = self.env['ir.default']._get('product.template', 'stock_type')
        self.assertEqual(stored_stock_type, 'forecast')

        retrieved = self.env['res.config.settings'].get_values()
        self.assertEqual(retrieved['location_type'], 'specific')
        self.assertEqual(retrieved['stock_location_id'], self.stock_location.id)
        self.assertEqual(retrieved['stock_type'], 'forecast')

    def test_10_res_config_settings_default_get_values(self):
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['location_type'], 'all')
        self.assertEqual(values['stock_type'], 'on_hand')
        self.assertEqual(values['stock_location_id'], self.stock_location.id)

    def test_11_controller_get_stock_info(self):
        controller = WebsiteSale()
        self.assertFalse(controller.get_stock_info(self.service_product))

        self._create_done_move(5, self.customer_location, self.stock_location)
        self.template.write({'location_type': 'all', 'stock_type': 'on_hand'})
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            self.assertEqual(controller.get_stock_info(self.template), 'in_stock')

        out_product = self.env['product.product'].create({
            'name': 'Out of stock product',
            'type': 'consu',
            'is_storable': True,
            'company_id': self.env.company.id,
        })
        out_template = out_product.product_tmpl_id.with_context(website_id=self.website.id)
        out_template.write({'location_type': 'all', 'stock_type': 'on_hand'})
        with MockRequest(self.env, website=self.website, website_sale_current_pl=self.pricelist.id):
            self.assertEqual(controller.get_stock_info(out_template), 'out_of_stock')
