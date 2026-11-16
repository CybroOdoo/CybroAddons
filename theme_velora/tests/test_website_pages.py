# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import HttpCase, tagged

from .common import apply_velora_theme


@tagged('post_install', '-at_install')
class TestVeloraPages(HttpCase):
    """Smoke tests: each themed page renders (this also exercises every view inheritance)."""

    def setUp(self):
        super().setUp()
        self.website = apply_velora_theme(self.env)

    def test_public_pages_render(self):
        for url in ('/', '/shop', '/about', '/collections', '/bestsellers', '/contactus', '/web/login'):
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 200, url)
                self.assertNotIn('fa-solid', response.text, url)
                self.assertNotIn('font-awesome', response.text.lower(), url)

    def test_homepage_has_newsletter_section(self):
        html = self.url_open('/').text
        self.assertIn('s_velora_newsletter', html)
        self.assertIn('Join the Velora Circle', html)

    def test_login_page_uses_velora_layout(self):
        html = self.url_open('/web/login').text
        self.assertIn('page-banner', html)
        self.assertIn('Welcome', html)
        self.assertIn('name="login"', html)
        self.assertIn('name="password"', html)

    def test_shop_has_desktop_search_form(self):
        html = self.url_open('/shop').text
        self.assertIn('o_wsale_products_searchbar_form', html)

    def test_logout_links_are_post_forms_for_logged_in_user(self):
        self.authenticate('admin', 'admin')
        html = self.url_open('/').text
        self.assertIn('action="/web/session/logout?redirect=/"', html)
        self.assertIn('method="POST"', html)
        self.assertIn('name="csrf_token"', html)
        self.assertNotIn('href="/web/session/logout', html)

    def test_pricelist_dropdown_in_shop_toolbar(self):
        """With several selectable pricelists, /shop shows the Pricelist dropdown."""
        # Odoo 20 only exposes `website_sale_pricelists` to templates when the
        # Pricelists feature (product.group_product_pricelist) is enabled.
        self.env.ref('base.group_user').write({
            'implied_ids': [(4, self.env.ref('product.group_product_pricelist').id)],
        })
        currency = self.website.currency_id
        pricelists = self.env['product.pricelist'].create([
            {'name': 'Velora Test A', 'selectable': True, 'currency_id': currency.id,
             'website_id': self.website.id},
            {'name': 'Velora Test B', 'selectable': True, 'currency_id': currency.id,
             'website_id': self.website.id},
        ])
        html = self.url_open('/shop').text
        self.assertIn('o_wsale_pricelist_selector', html)
        for pricelist in pricelists:
            self.assertIn(f'/shop/change_pricelist/{pricelist.id}', html)