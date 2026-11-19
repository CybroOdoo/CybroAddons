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

from odoo.tests import tagged

from .common import ClassicStoreHttpCase


@tagged('post_install', '-at_install')
class TestClassicStoreShop(ClassicStoreHttpCase):

    def test_shop_page_renders_product(self):
        """/shop renders with the theme templates and lists the product."""
        doc = self.get_html('/shop?search=ClassicStoreTest')
        self.assertTrue(
            doc.xpath("//*[contains(@class, 'oe_product')]"),
            "The shop grid should contain the test product")
        self.assertIn(
            'ClassicStoreTest Product',
            ' '.join(doc.xpath("//*[contains(@class, 'oe_product')]//text()")))

    def test_product_links_open_product_page(self):
        """Image, title and category links must point to the product page
        (Odoo 20: `product_href` must be passed to products_item)."""
        doc = self.get_html('/shop?search=ClassicStoreTest')
        url = self.product.website_url
        image_links = doc.xpath(
            "//a[contains(@class, 'oe_product_image_link')]/@href")
        self.assertTrue(image_links, "No product image link found")
        for href in image_links:
            self.assertTrue(
                href.startswith(url),
                f"Image link {href!r} should open {url!r}")
        title_links = doc.xpath(
            "//*[contains(@class, 'o_wsale_products_item_title')]//a/@href")
        self.assertTrue(title_links)
        for href in title_links:
            self.assertTrue(href.startswith(url))

    def test_product_page_renders_public(self):
        """Product page must render for a public visitor (no KeyError on
        `prevent_sale`, `object`, ...)."""
        doc = self.get_html(self.product.website_url)
        self.assertTrue(doc.xpath("//*[@id='product_detail']"))
        self.assertTrue(
            doc.xpath("//*[@id='pills-contact']"),
            "The theme review tab should be rendered")

    def test_product_page_renders_logged_in(self):
        self.authenticate('admin', 'admin')
        doc = self.get_html(self.product.website_url)
        self.assertTrue(doc.xpath("//*[@id='product_detail']"))

    def test_product_page_has_quantity_selector(self):
        doc = self.get_html(self.product.website_url)
        self.assertTrue(
            doc.xpath("//*[contains(@class, 'css_quantity')]"),
            "The quantity selector should be rendered")

    def test_shop_category_page_renders(self):
        """The category link below the product image must work."""
        self.get_html(f'/shop/category/{self.env["ir.http"]._slug(self.category)}')

    def test_product_comment_view_disabled_by_theme(self):
        """The theme post-copy hook disables the core review block."""
        view = self.website.viewref('website_sale.product_comment')
        self.assertFalse(view.active)
