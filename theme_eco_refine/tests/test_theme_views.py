# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestThemeViews(TransactionCase):
    """Tests that the theme views are applied and combine correctly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.env.ref('base.module_theme_eco_refine')._theme_load(cls.website)

    def _combined_header(self):
        root = self.env.ref('website.template_header_default').with_context(
            website_id=self.website.id)
        return etree.fromstring(root.get_combined_arch())

    def test_theme_views_exist(self):
        for xmlid in (
            'theme_eco_refine.template_header_refurbished',
            'theme_eco_refine.header_search_box_remove_default',
            'theme_eco_refine.website_contactus_refurbished',
        ):
            self.assertTrue(self.env.ref(xmlid).exists(), xmlid)

    def test_theme_views_copied_to_website(self):
        """Loading the theme creates active website-specific views."""
        view = self.env['ir.ui.view'].search([
            ('key', '=', 'theme_eco_refine.template_header_refurbished'),
            ('website_id', '=', self.website.id),
        ])
        self.assertTrue(view)
        self.assertTrue(view.active)
        self.assertEqual(view.inherit_id.key,
                         'website_sale.template_header_default')

    def test_combined_header_has_custom_block(self):
        arch = self._combined_header()
        self.assertEqual(len(arch.xpath("//div[hasclass('ref-header')]")), 1)
        for call in ('website_sale.header_cart_link',
                     'website_sale.header_wishlist_link'):
            nodes = arch.xpath("//t[@t-call='%s']" % call)
            self.assertEqual(len(nodes), 1, call)
            self.assertTrue(
                nodes[0].xpath("ancestor::div[hasclass('ref-header')]"), call)

    def test_core_user_and_signin_calls_moved(self):
        arch = self._combined_header()
        for call in ('portal.user_dropdown',
                     'portal.placeholder_user_sign_in'):
            nodes = arch.xpath("//t[@t-call='%s']" % call)
            self.assertEqual(len(nodes), 1, call)
            self.assertTrue(
                nodes[0].xpath("ancestor::div[hasclass('ref-header')]"), call)

    def test_default_search_box_call_removed(self):
        arch = self._combined_header()
        self.assertFalse(
            arch.xpath("//t[@t-call='website.placeholder_header_search_box']"))
        self.assertTrue(
            arch.xpath("//t[@t-call='website.header_search_box']"))

    def test_product_form_view_loads(self):
        views = self.env['ir.ui.view'].search([
            ('model', '=', 'product.template'),
            ('arch_db', 'ilike', 'product_spec'),
        ])
        self.assertTrue(views, "No product form view shows product_spec")
        for view in views:
            etree.fromstring(view.get_combined_arch())
    def test_footer_keeps_core_anchor(self):
        """Core views (e.g. the cookie policy link) hook on div#footer."""
        root = self.env.ref('website.layout').with_context(
            website_id=self.website.id)
        arch = etree.fromstring(root.get_combined_arch())
        self.assertEqual(len(arch.xpath("//div[@id='footer']")), 1)
        self.assertEqual(len(arch.xpath("//footer[@id='ref-footer']")), 1)