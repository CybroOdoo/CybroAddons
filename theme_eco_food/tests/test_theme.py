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

"""Tests for Eco Food theme models and website endpoints."""

# pylint: disable=import-error,no-name-in-module
from lxml import html

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestEcoFoodWebsite(HttpCase):
    """Verify JSON endpoints used by Eco Food website snippets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        website = cls.env["website"].search([], limit=1)
        theme = cls.env["ir.module.module"].search([("name", "=", "theme_eco_food")])
        website.theme_id = theme
        theme._theme_load(website)  # pylint: disable=protected-access

    @staticmethod
    def _jsonrpc_params(**params):
        return {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": params,
        }

    def _call_jsonrpc(self, path, **params):
        response = self.url_open(
            path,
            json=self._jsonrpc_params(**params),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("error", payload)
        return payload["result"]

    def test_product_snippet_endpoints(self):
        """Return configured products and testimonials from snippet routes."""
        product = self.env["product.template"].create(
            {
                "name": "Eco Food Endpoint Product",
                "website_published": True,
            }
        )
        self.env.ref("theme_eco_food.best_seller_product").write(
            {
                "product_tmpl_ids": [Command.set([product.id])],
            }
        )
        self.env.ref("theme_eco_food.featured_product").write(
            {
                "product_tmpl_ids": [Command.set([product.id])],
            }
        )
        self.env.ref("theme_eco_food.recently_added_product").write(
            {
                "product_tmpl_ids": [Command.set([product.id])],
            }
        )
        self.env.ref("theme_eco_food.new_arrival_product").write(
            {
                "product_tmpl_ids": [Command.set([product.id])],
            }
        )

        partner = self.env["res.partner"].create(
            {
                "name": "Eco Food Test Customer",
                "email": "eco-food-customer@example.com",
            }
        )
        self.env["ecofood.testimonial"].create(
            {
                "partner_id": partner.id,
                "review": "A test review",
            }
        )

        bestseller = self._call_jsonrpc("/get_best_seller")
        self.assertEqual([item["id"] for item in bestseller], [product.id])
        self.assertEqual(bestseller[0]["product_id"], product.product_variant_id.id)

        featured = self._call_jsonrpc("/get_featured_products")
        self.assertEqual(featured["slide1"][0]["id"], product.id)

        recent = self._call_jsonrpc("/get_recently_added_products")
        self.assertEqual(recent["slide1"][0]["id"], product.id)

        arrivals = self._call_jsonrpc("/get_new_arrivals")
        self.assertEqual([item["id"] for item in arrivals], [product.id])
        self.assertEqual(arrivals[0]["product_id"], product.product_variant_id.id)

        testimonials = self._call_jsonrpc("/get_testimonials")
        self.assertEqual(testimonials["slide1"][0]["name"], partner.name)
        self.assertEqual(testimonials["slide1"][0]["review"], "A test review")

    def test_product_selection_route(self):
        """Keep shop category selection in the visitor request session."""
        category = self.env["product.public.category"].create(
            {"name": "Eco Food Selection Category"}
        )
        selected = self.env["product.template"].create(
            {
                "name": "Eco Food Session Selected Product",
                "public_categ_ids": [Command.set([category.id])],
            }
        )
        self.assertTrue(
            self._call_jsonrpc(
                "/theme_eco_food/product_selections",
                all_products=False,
                category_ids=[category.id],
            )
        )
        self.assertNotIn("selected_att", selected._fields)
        self.assertTrue(
            self._call_jsonrpc(
                "/theme_eco_food/product_selections",
                all_products=True,
                category_ids=[],
            )
        )

    def test_newsletter_rejects_invalid_and_duplicate_emails(self):
        """Reject invalid and duplicate newsletter addresses."""
        self.assertFalse(
            self._call_jsonrpc("/subscribe_newsletter", email="not-an-email")
        )
        self.assertTrue(
            self._call_jsonrpc(
                "/subscribe_newsletter", email="eco-food-test@example.com"
            )
        )
        self.assertFalse(
            self._call_jsonrpc(
                "/subscribe_newsletter", email="ECO-FOOD-TEST@example.com"
            )
        )

    def test_shop_category_filter_and_reset(self):
        """Render the shop with visitor categories, child categories and pagination."""
        self.env["website"].search([], limit=1).shop_ppg = 20
        category = self.env["product.public.category"].create(
            {"name": "Review Produce"}
        )
        child = self.env["product.public.category"].create(
            {
                "name": "Review Fruit",
                "parent_id": category.id,
            }
        )
        products = self.env["product.template"].create(
            [
                {
                    "name": f"Review Selected Fruit {index:02d}",
                    "website_published": True,
                    "public_categ_ids": [Command.set(child.ids)],
                }
                for index in range(22)
            ]
        )
        other = self.env["product.template"].create(
            {
                "name": "Review Other Product",
                "website_published": True,
            }
        )
        self._call_jsonrpc(
            "/theme_eco_food/product_selections",
            category_ids=category.ids,
        )
        response = self.url_open("/shop?ppg=20")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        names = tree.xpath("//div[contains(@class, 'p_name')]/a/text()")
        names = [name.strip() for name in names if name.strip()]
        self.assertEqual(len(names), 20)
        self.assertNotIn(other.name, names)
        self.assertTrue(set(names).issubset(set(products.mapped("name"))))
        response = self.url_open("/shop/page/2?ppg=20")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        page_names = tree.xpath("//div[contains(@class, 'p_name')]/a/text()")
        self.assertEqual(len([name for name in page_names if name.strip()]), 2)
        self._call_jsonrpc("/theme_eco_food/product_selections", category_ids=[])
        response = self.url_open("/shop?search=Review")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'class="p_name"', response.content)
        self._call_jsonrpc("/theme_eco_food/product_selections", all_products=True)
        response = self.url_open("/shop?search=Review+Other+Product")
        self.assertEqual(response.status_code, 200)
        self.assertIn(other.name, response.text)

    def test_snippets_exclude_unpublished_products(self):
        """Never expose an unpublished product configured in a public snippet."""
        hidden = self.env["product.template"].create({"name": "Private Review Product"})
        for xmlid in (
            "best_seller_product",
            "featured_product",
            "recently_added_product",
            "new_arrival_product",
        ):
            self.env.ref(f"theme_eco_food.{xmlid}").product_tmpl_ids = hidden
        self.assertEqual(self._call_jsonrpc("/get_best_seller"), [])
        self.assertEqual(self._call_jsonrpc("/get_featured_products"), {})
        self.assertEqual(self._call_jsonrpc("/get_recently_added_products"), {})
        self.assertEqual(self._call_jsonrpc("/get_new_arrivals"), [])

    def test_newsletter_form_is_wired(self):
        """The footer contains the input and control used by the signup interaction."""
        response = self.url_open("/shop")
        self.assertEqual(response.status_code, 200)
        self.assertIn("newsletter-email", response.text)
        self.assertIn('id="newsletter"', response.text)
        self.assertIn('id="newsletter-status"', response.text)

    def test_browser_newsletter_signup(self):
        """Exercise the real footer interaction and compiled frontend assets in Chrome."""
        self.browser_js(
            "/shop",
            """
            (async () => {
                const input = document.querySelector('.newsletter-email');
                const button = document.querySelector('#newsletter');
                const status = document.querySelector('#newsletter-status');
                if (!input || !button || !status) {
                    throw new Error('Newsletter form is missing');
                }
                input.value = `browser-review-${Date.now()}@example.com`;
                button.click();
                for (let attempt = 0; attempt < 20; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 250));
                    if (status.textContent.includes('Thank you for subscribing')) {
                        console.log('test successful');
                        return;
                    }
                }
                throw new Error('Newsletter interaction did not subscribe: ' + status.textContent);
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_cart_quantity_and_remove_contract(self):
        """Render and update a populated themed cart using native Odoo 20 controls."""
        product = self.env["product.template"].create(
            {
                "name": "Review Cart Product",
                "website_published": True,
                "list_price": 12,
            }
        )
        self._call_jsonrpc(
            "/shop/cart/add",
            product_template_id=product.id,
            product_id=product.product_variant_id.id,
            quantity=1,
        )
        response = self.url_open("/shop/cart")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        inputs = tree.xpath(
            "//*[@id='cart_products']//*[contains(@class, 'js_quantity')]"
        )
        self.assertTrue(inputs)
        line_id = int(inputs[0].get("data-line-id"))
        result = self._call_jsonrpc(
            "/shop/cart/update",
            line_id=line_id,
            product_id=product.product_variant_id.id,
            quantity=2,
        )
        self.assertEqual(result["cart_quantity"], 2)
        result = self._call_jsonrpc(
            "/shop/cart/update",
            line_id=line_id,
            product_id=product.product_variant_id.id,
            quantity=0,
        )
        self.assertEqual(result["cart_quantity"], 0)

    def test_browser_dynamic_snippets(self):
        """Render all five snippets and initialize the four carousels in Chrome."""
        product = self.env["product.template"].create(
            {
                "name": "Review Browser Snippet Product",
                "website_published": True,
            }
        )
        for xmlid in (
            "best_seller_product",
            "featured_product",
            "recently_added_product",
            "new_arrival_product",
        ):
            self.env.ref(f"theme_eco_food.{xmlid}").product_tmpl_ids = product
        partner = self.env["res.partner"].create({"name": "Review Browser Customer"})
        self.env["ecofood.testimonial"].create(
            {
                "partner_id": partner.id,
                "review": "Review browser testimonial",
            }
        )
        snippets = (
            "eco_food_best_seller",
            "eco_food_featured_products",
            "eco_food_new_arrival",
            "eco_food_recently_added_products",
            "eco_food_testimonial",
        )
        calls = "".join(
            f'<t t-call="theme_eco_food.{snippet}"/>' for snippet in snippets
        )
        self.env["website.page"].create(
            {
                "name": "Eco Food Browser Review",
                "type": "qweb",
                "key": "theme_eco_food.browser_review",
                "url": "/eco-food-browser-review",
                "website_id": self.env["website"].search([], limit=1).id,
                "is_published": True,
                "arch": f'<t t-call="website.layout"><div id="wrap">{calls}</div></t>',
            }
        )
        self.browser_js(
            "/eco-food-browser-review",
            """
            (async () => {
                for (let attempt = 0; attempt < 40; attempt++) {
                    const carousels = document.querySelectorAll('.owl-loaded');
                    const bestSeller = document.querySelector('.best_seller_products');
                    const testimonial = document.querySelector('.testimonial_carousel');
                    if (carousels.length === 4 &&
                        bestSeller?.textContent.includes('Review Browser Snippet Product') &&
                        testimonial?.textContent.includes('Review browser testimonial')) {
                        if (document.querySelector('#wrap .b_product a a')) {
                            throw new Error('Product cards contain nested links');
                        }
                        for (const selector of [
                            '.best_seller_products', '.featured_product_carousal',
                            '.recently_added_carousel',
                        ]) {
                            const card = document.querySelector(selector + ' .b_product');
                            const imageLink = card?.querySelector('.img_wrapper > a');
                            const detailsLink = card?.querySelector('a.product_info');
                            if (!imageLink || !detailsLink || imageLink.href !== detailsLink.href) {
                                throw new Error('Product image and details links are not wired: ' + selector);
                            }
                            const originalOpen = window.open;
                            let openedUrl;
                            try {
                                window.open = (url) => { openedUrl = url; };
                                card.querySelector('.eco-food-card-content').dispatchEvent(
                                    new MouseEvent('click', { bubbles: true, ctrlKey: true })
                                );
                            } finally {
                                window.open = originalOpen;
                            }
                            if (openedUrl !== detailsLink.getAttribute('href')) {
                                throw new Error('Whole-card navigation is not wired: ' + selector);
                            }
                        }
                        for (const rating of document.querySelectorAll('#wrap .p_rating > .o_website_rating_static')) {
                            if (rating.title !== '0' || rating.querySelectorAll('[data-icon="star"]').length !== 5) {
                                throw new Error('Product rating is not bound to the configured product');
                            }
                        }
                        const cartQuantity = async () => {
                            const response = await fetch('/shop/cart');
                            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                            return Array.from(page.querySelectorAll('#cart_products input.js_quantity'))
                                .reduce((total, input) => total + Number(input.value), 0);
                        };
                        for (const selector of [
                            '.best_seller_products .cart-btn',
                            '.new_arrival_carousel .owl-item.cloned .cart-btn',
                        ]) {
                            const button = document.querySelector(selector);
                            if (!button) throw new Error('Missing snippet cart button: ' + selector);
                            const before = await cartQuantity();
                            button.click();
                            let added = false;
                            for (let retry = 0; retry < 40; retry++) {
                                await new Promise(resolve => setTimeout(resolve, 250));
                                const quantity = await cartQuantity();
                                if (quantity > before) { added = true; break; }
                            }
                            if (!added) throw new Error('Snippet cart button did not add a product: ' + selector);
                        }
                        console.log('test successful');
                        return;
                    }
                    await new Promise(resolve => setTimeout(resolve, 250));
                }
                throw new Error('The five snippets did not render with four active carousels');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_browser_shop_add_to_cart(self):
        """Click the themed shop card and verify the resulting cart line."""
        product = self.env["product.template"].create({
            "name": "Eco Food Cart Browser Product",
            "website_published": True,
            "list_price": 10,
        })
        self.browser_js(
            f"/shop?search={product.name}",
            """
            (async () => {
                const button = document.querySelector('.cart-btn');
                if (!button) throw new Error('Shop cart button is missing');
                button.click();
                for (let attempt = 0; attempt < 40; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 250));
                    const response = await fetch('/shop/cart');
                    const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                    if (page.querySelector('#cart_products')?.textContent.includes('Eco Food Cart Browser Product')) {
                        console.log('test successful');
                        return;
                    }
                }
                throw new Error('Clicking the shop card did not add the product to the cart');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_browser_configurable_shop_cart(self):
        """Configure a shop-card product and add the selected variant to the cart."""
        attribute = self.env['product.attribute'].create({
            'name': 'Eco Desk Finish',
            'create_variant': 'dynamic',
        })
        values = self.env['product.attribute.value'].create([
            {'name': 'Natural', 'attribute_id': attribute.id},
            {'name': 'White', 'attribute_id': attribute.id},
        ])
        product = self.env['product.template'].create({
            'name': 'Eco Configurable Desk',
            'website_published': True,
            'list_price': 75,
            'attribute_line_ids': [Command.create({
                'attribute_id': attribute.id,
                'value_ids': [Command.set(values.ids)],
            })],
        })
        self.browser_js(
            f'/shop?search={product.name}',
            """
            (async () => {
                const cartButton = document.querySelector('.cart-btn');
                if (!cartButton) throw new Error('Configurable product cart button is missing');
                cartButton.querySelector('i').click();
                let confirm;
                for (let attempt = 0; attempt < 40; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 250));
                    confirm = document.querySelector('[name="website_sale_product_configurator_continue_button"]');
                    if (confirm && !confirm.disabled) break;
                }
                if (!confirm || confirm.disabled) throw new Error('Product configurator did not open');
                confirm.click();
                for (let attempt = 0; attempt < 40; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 250));
                    const response = await fetch('/shop/cart');
                    const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                    if (page.querySelector('#cart_products')?.textContent.includes('Eco Configurable Desk')) {
                        console.log('test successful');
                        return;
                    }
                }
                throw new Error('Configured desk was not added to the cart');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_browser_product_page_cart_and_compare(self):
        """Use the product-page buttons with the selected variant and quantity."""
        attribute = self.env['product.attribute'].create({'name': 'Eco Desk Color'})
        values = self.env['product.attribute.value'].create([
            {'name': 'White', 'attribute_id': attribute.id},
            {'name': 'Black', 'attribute_id': attribute.id},
        ])
        product = self.env['product.template'].create({
            'name': 'Eco Product Page Desk',
            'website_published': True,
            'list_price': 75,
            'attribute_line_ids': [Command.create({
                'attribute_id': attribute.id,
                'value_ids': [Command.set(values.ids)],
            })],
        })
        self.browser_js(
            product.website_url,
            """
            (async () => {
                const compare = document.querySelector('.o_add_compare, .o_add_compare_dyn');
                const add = document.querySelector('button[name="add_to_cart"]');
                if (!compare || !add) throw new Error('Product-page action buttons are missing');
                compare.click();
                for (let attempt = 0; attempt < 40; attempt++) {
                    if (compare.disabled && document.cookie.includes('comparison_product_ids=')) break;
                    await new Promise(resolve => setTimeout(resolve, 250));
                }
                if (!compare.disabled || !document.cookie.includes('comparison_product_ids=')) {
                    throw new Error('The selected variant was not added to comparison');
                }
                document.querySelector('input[name="add_qty"]').value = '2';
                add.click();
                for (let attempt = 0; attempt < 40; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 250));
                    const response = await fetch('/shop/cart');
                    const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                    const cart = page.querySelector('#cart_products');
                    if (cart?.textContent.includes('Eco Product Page Desk') &&
                        cart.querySelector('input.js_quantity')?.value === '2') {
                        console.log('test successful');
                        return;
                    }
                }
                throw new Error('Product-page Add to Cart did not preserve the selected quantity');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_browser_header_layout(self):
        """Keep the header above page content for visitors and website editors."""
        self.env['website.page'].create({
            'name': 'Eco Header Layout',
            'type': 'qweb',
            'key': 'theme_eco_food.header_layout_test',
            'url': '/eco-header-layout-test',
            'website_id': self.env['website'].search([], limit=1).id,
            'is_published': True,
            'arch': '<t t-call="website.layout"><div id="wrap">'
                    '<section id="eco-layout-content" style="min-height:200vh">'
                    '<h1>Header layout check</h1></section></div></t>',
        })
        code = """
            (async () => {
                const header = document.querySelector('#eco_food_header');
                const content = document.querySelector('#eco-layout-content');
                const navbar = header.querySelector('.navbar');
                const topbar = header.querySelector('.top_bar1');
                const bounds = header.getBoundingClientRect();
                if (content.getBoundingClientRect().top < bounds.bottom - 1) {
                    throw new Error('Theme header overlaps page content');
                }
                for (const row of [navbar, topbar]) {
                    if (Math.abs(row.getBoundingClientRect().width - bounds.width) > 2) {
                        throw new Error('Header row does not fill its container');
                    }
                }
                document.querySelector('#wrapwrap').scrollTop = 200;
                await new Promise(resolve => setTimeout(resolve, 300));
                if (getComputedStyle(header.querySelector('.topbar')).position === 'fixed') {
                    throw new Error('Scrolled navigation detaches from the header');
                }
                console.log('test successful');
            })();
        """
        for login in (None, 'admin'):
            self.browser_js(
                '/eco-header-layout-test',
                code,
                login=login,
                ready="document.body.getAttribute('is-ready') === 'true'",
                timeout=60,
            )

    def test_browser_theme_background_images(self):
        """Load the original theme artwork from the compiled Odoo 19 stylesheet."""
        snippets = ['ecofood_banner', 'eco_food_client', 'eco_food_ad', 'eco_food_website_ad', 'eco_food_service']
        calls = ''.join(f'<t t-call="theme_eco_food.{name}"/>' for name in snippets)
        self.env['website.page'].create({
            'name': 'Eco Reference Artwork',
            'type': 'qweb',
            'key': 'theme_eco_food.reference_artwork_test',
            'url': '/eco-reference-artwork-test',
            'website_id': self.env['website'].search([], limit=1).id,
            'is_published': True,
            'arch': f'<t t-call="website.layout"><div id="wrap">{calls}</div></t>',
        })
        self.browser_js(
            '/eco-reference-artwork-test',
            r"""
            (async () => {
                const background = document.querySelector('.banner_bg1');
                const banner = background.getBoundingClientRect();
                if (banner.width < 300 || banner.height < 100) {
                    throw new Error('Original banner layout is missing');
                }
                const urls = new Set();
                for (const element of document.querySelectorAll('#wrap *')) {
                    const image = getComputedStyle(element).backgroundImage;
                    for (const match of image.matchAll(/url\(["']?([^"')]+)["']?\)/g)) {
                        if (match[1].includes('/theme_eco_food/')) urls.add(match[1]);
                    }
                }
                for (const image of document.querySelectorAll('img[src*="/theme_eco_food/"]')) {
                    urls.add(image.src);
                }
                if (urls.size < 8) throw new Error('Theme artwork is missing from the page');
                for (const url of urls) {
                    if (url.includes('/scss/')) throw new Error('Image URL incorrectly resolved from SCSS: ' + url);
                    await new Promise((resolve, reject) => {
                        const image = new Image();
                        image.onload = resolve;
                        image.onerror = () => reject(new Error('Broken theme image: ' + url));
                        image.src = url;
                    });
                }
                console.log('test successful');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
            timeout=60,
        )

    def test_browser_theme_background_images_mobile(self):
        """Check the reference artwork and banner at a mobile viewport."""
        self.browser_size = '390x844'
        self.test_browser_theme_background_images()

    def test_browser_contact_layout(self):
        """Keep the migrated contact margins and form at desktop and mobile sizes."""
        for size in ('1366x900', '390x844'):
            self.browser_size = size
            self.browser_js(
                '/contactus',
                """
                const contact = document.querySelector('.contact');
                const form = contact?.querySelector('form');
                if (!contact || !form) throw new Error('The contact section or form is missing');
                const style = getComputedStyle(contact);
                if (style.marginLeft !== '15px' || style.marginRight !== '15px') {
                    throw new Error('The migrated contact margins changed');
                }
                console.log('test successful');
                """,
                ready="document.body.getAttribute('is-ready') === 'true'",
                timeout=60,
            )

    def test_browser_dynamic_snippets_mobile(self):
        """Keep snippet links, ratings, carousels, and cart actions working on mobile."""
        self.browser_size = '390x844'
        self.test_browser_dynamic_snippets()
