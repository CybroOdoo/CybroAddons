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
from odoo.tests import TransactionCase, tagged

from .common import apply_velora_theme


@tagged('post_install', '-at_install')
class TestThemeViews(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = apply_velora_theme(cls.env)
        cls.ctx_env = cls.env(context=dict(cls.env.context, website_id=cls.website.id))

    def _theme_views(self):
        """Website copies of the theme views (they have no ir.model.data entry)."""
        return self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_velora.%'),
            ('website_id', '=', self.website.id),
        ])

    def test_theme_views_exist(self):
        views = self._theme_views()
        self.assertTrue(views, 'Theme Velora must register its views')

    def test_inheriting_views_apply_to_parent(self):
        """Every inheriting theme view must still locate its xpath targets in the parent
        (catches 'Element ... cannot be located in parent view' after an Odoo upgrade)."""
        roots = self.env['ir.ui.view']
        for view in self._theme_views().filtered(lambda v: v.inherit_id and v.active):
            root = view
            while root.inherit_id:
                root = root.inherit_id
            roots |= root
        self.assertTrue(roots)
        for root in roots:
            with self.subTest(root=root.xml_id or root.name):
                root = root.with_context(website_id=self.website.id)
                self.assertTrue(root._get_combined_arch() is not None)

    def test_login_layout_override(self):
        """After website.login_layout, the Velora banner replaces the login container."""
        layout = self.ctx_env.ref('web.login_layout')
        arch = layout._get_combined_arch()
        self.assertTrue(arch.xpath("//t[@t-call='website.layout']"))
        self.assertTrue(arch.xpath("//section[hasclass('page-banner')]"))
        self.assertFalse(arch.xpath("//div[hasclass('oe_website_login_container')]"))

    def test_shop_toolbar_has_pricelist_selector_hook(self):
        arch = self.ctx_env.ref('website_sale.products').get_combined_arch()
        self.assertIn('o_wsale_pricelist_selector', arch)
        self.assertIn('/shop/change_pricelist/', arch)

    def test_header_logout_is_post_form(self):
        arch = self.ctx_env.ref('website.layout').get_combined_arch()
        self.assertIn('/web/session/logout', arch)
        self.assertNotIn('href="/web/session/logout', arch)
        self.assertIn('method="POST"', arch)