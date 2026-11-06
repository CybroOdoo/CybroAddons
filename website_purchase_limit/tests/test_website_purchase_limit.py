# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestWebsitePurchaseLimit(HttpCase):
    
    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_bool('website_purchase_limit.enabled_limit', True)
        self.env['ir.config_parameter'].sudo().set_float('website_purchase_limit.purchase_limit', 1000.0)

        self.product_below = self.env['product.product'].create({
            'name': 'Limit Product Below',
            'list_price': 500.0,
            'website_published': True,
        })
        self.product_above = self.env['product.product'].create({
            'name': 'Limit Product Above',
            'list_price': 1500.0,
            'website_published': True,
        })
        self.product_exact = self.env['product.product'].create({
            'name': 'Limit Product Exact',
            'list_price': 1000.0,
            'website_published': True,
        })
        
    def test_purchase_limit_below(self):
        self.start_tour("/shop", "website_purchase_limit_test_below", login="admin")
        
    def test_purchase_limit_above(self):
        self.start_tour("/shop", "website_purchase_limit_test_above", login="admin")

    def test_purchase_limit_disabled(self):
        self.env['ir.config_parameter'].sudo().set_bool('website_purchase_limit.enabled_limit', False)
        self.start_tour("/shop", "website_purchase_limit_test_disabled", login="admin")

    def test_purchase_limit_exact(self):
        self.start_tour("/shop", "website_purchase_limit_test_exact", login="admin")
