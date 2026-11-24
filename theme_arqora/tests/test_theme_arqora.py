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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json

from odoo import Command
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

PNG = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA'
    '60e6kgAAAABJRU5ErkJggg==')


@tagged('post_install', '-at_install')
class TestThemeArqora(HttpCase):
    """Test the pages, header templates and dynamic blocks of the theme."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme on the test website."""
        super().setUpClass()
        website = cls.env['website'].search([], limit=1)
        theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_arqora')], limit=1)
        theme._theme_load(website)
        cls.website = website

    def test_pages_render(self):
        """Every page of the theme answers with its Arqora blocks."""
        for url in ('/', '/about', '/services', '/projects', '/materials',
                    '/resources', '/legal', '/contactus', '/shop'):
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn('aq-', response.text, url)

    def test_home_overlay_header(self):
        """The home page uses the header overlay of the hero room."""
        pages = self.env['website.page'].search([
            ('url', '=', '/'), ('website_id', '=', self.website.id)])
        self.theme_utils = self.env['theme.utils'].with_context(
            website_id=self.website.id)
        theme = self.env['ir.module.module'].search(
            [('name', '=', 'theme_arqora')], limit=1)
        self.theme_utils._theme_arqora_post_copy(theme)
        self.assertTrue(pages.header_overlay)

    def test_menus(self):
        """The theme menus keep their link."""
        urls = self.website.menu_id.child_id.mapped('url')
        for url in ('/shop', '/services', '/projects', '/about', '/contactus'):
            self.assertIn(url, urls)

    def test_dynamic_blocks(self):
        """The collection and product routes render their cards."""
        self.authenticate(None, None)
        for route in ('collections', 'signature'):
            response = self.make_jsonrpc_request('/theme_arqora/%s' % route, {})
            self.assertIn('html', response)

    def test_contact_form_creates_lead(self):
        """The enquiry form creates a lead and goes to the thank-you page."""
        response = self.url_open('/contactus')
        self.assertIn('data-model_name="crm.lead"', response.text)
        self.assertIn('data-success-page="/contactus-thank-you"',
                      response.text)
        self.assertIn('s_website_form_send', response.text)
        thanks = self.url_open('/contactus-thank-you')
        self.assertEqual(thanks.status_code, 200)
        self.assertIn('Thank you.', thanks.text)
        self.authenticate(None, None)
        csrf = self.csrf_token()
        result = self.url_open('/website/form/crm.lead', data={
            'csrf_token': csrf,
            'contact_name': 'Test Architect',
            'email_from': 'architect@example.com',
            'partner_name': 'Test Studio',
            'name': 'Architect enquiry',
            'description': 'Test enquiry',
            'product': 'ORION (Brushed brass)',
        })
        self.assertEqual(result.status_code, 200)
        lead = self.env['crm.lead'].search(
            [('email_from', '=', 'architect@example.com')])
        self.assertTrue(lead)
        self.assertEqual(lead.name, 'Architect enquiry')
        self.assertIn('ORION (Brushed brass)', lead.description)

    def test_request_a_quote(self):
        """A quote-only product gets Request a Quote, not the cart."""
        self.website.write({
            'prevent_sale': True, 'prevent_sale_for': 'quote_only'})
        quote = self.env['product.template'].create({
            'name': 'Quote Only Lamp', 'list_price': 500,
            'is_published': True, 'quote_only': True})
        normal = self.env['product.template'].create({
            'name': 'Normal Lamp', 'list_price': 50, 'is_published': True})
        self.assertTrue(
            self.website._prevent_product_sale(quote, False))
        self.assertFalse(
            self.website._prevent_product_sale(normal, False))
        self.assertFalse(
            quote.product_variant_id.with_context(
                website_id=self.website.id)._is_add_to_cart_allowed())
        self.assertIn('product={}'.format(quote.id),
                      self.website._arqora_quote_url(quote, 'Brushed brass'))
        self.assertIn('finish=Brushed+brass',
                      self.website._arqora_quote_url(quote, 'Brushed brass'))
        info = self.make_jsonrpc_request(
            '/theme_arqora/quote_product', {'product_id': quote.id})
        self.assertEqual(info['name'], 'Quote Only Lamp')
        page = self.url_open(quote.website_url)
        self.assertIn('id="quote-btn"', page.text)
        self.assertIn('aq-pdp-quote', page.text)
        self.assertNotIn('aq-download__title', page.text)
        self.env['product.document'].create({
            'name': 'Spec sheet.pdf', 'raw': b'PDF',
            'res_model': 'product.template', 'res_id': quote.id,
            'attached_on_sale': 'shown_on_product_page'})
        page = self.url_open(quote.website_url)
        self.assertIn('aq-download__title', page.text)
        self.assertIn('Spec sheet.pdf', page.text)
        self.assertEqual(page.text.count('Spec sheet.pdf'), 2)
        self.assertNotIn('o_add_wishlist_dyn', page.text)
        normal_page = self.url_open(normal.website_url)
        self.assertIn('o_add_wishlist_dyn', normal_page.text)
        self.assertNotIn('aq-pdp__assure', normal_page.text)
        contact = self.url_open('/contactus')
        self.assertIn('name="product"', contact.text)
        self.assertIn('aq-product-ref', contact.text)
        self.assertIn('data-aq-key="architect"', contact.text)

    def test_quote_product_route_without_product(self):
        """The quote route answers an empty dict for an unknown or hidden product."""
        hidden = self.env['product.template'].create({
            'name': 'Hidden Lamp', 'list_price': 10, 'is_published': False})
        for product_id in (0, 999999999, hidden.id):
            info = self.make_jsonrpc_request(
                '/theme_arqora/quote_product', {'product_id': product_id})
            self.assertFalse(info, product_id)

    def test_wishlist_refuses_quote_product(self):
        """A quote-only product cannot be added to the wishlist."""
        quote = self.env['product.template'].create({
            'name': 'Quote Wishlist Lamp', 'list_price': 500,
            'is_published': True, 'quote_only': True})
        normal = self.env['product.template'].create({
            'name': 'Normal Wishlist Lamp', 'list_price': 50,
            'is_published': True})
        self.authenticate(None, None)
        with mute_logger('odoo.http'):
            response = self.url_open(
                '/shop/wishlist/add', headers={
                    'Content-Type': 'application/json'},
                data=json.dumps({'params': {
                    'product_id': quote.product_variant_id.id}}))
        self.assertIn('error', response.json())
        self.assertIn('sold on quotation', json.dumps(response.json()))
        self.assertFalse(self.env['product.wishlist'].search(
            [('product_id', '=', quote.product_variant_id.id)]))
        response = self.url_open(
            '/shop/wishlist/add', headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {
                'product_id': normal.product_variant_id.id}}))
        self.assertNotIn('error', response.json())

    def test_prevent_sale_without_quote_mode(self):
        """Other prevent-sale modes keep the standard rule."""
        self.website.write({
            'prevent_sale': True, 'prevent_sale_for': 'zero_price'})
        quote = self.env['product.template'].create({
            'name': 'Quote Zero Lamp', 'list_price': 500, 'quote_only': True})
        self.assertFalse(self.website._prevent_product_sale(quote, False))
        self.assertTrue(self.website._prevent_product_sale(quote, True))
        self.assertTrue(self.website._arqora_is_quote_only(
            quote.product_variant_id))
        self.assertEqual(
            self.website._arqora_quote_url(), '/contactus?type=architect')

    def test_price_format(self):
        """Prices are shown whole, with decimals, before or after the sign."""
        usd = self.env.ref('base.USD')
        eur = self.env.ref('base.EUR')
        usd.position = 'before'
        eur.position = 'after'
        self.assertEqual(self.website._arqora_price(2450, usd), '$2,450')
        self.assertEqual(self.website._arqora_price(2450.5, usd), '$2,450.50')
        self.assertEqual(
            self.website._arqora_price(2450, eur), '2,450\N{NO-BREAK SPACE}€')
        self.assertTrue(self.website._arqora_price(10))

    def test_collections_data(self):
        """Collections skip empty categories and use the category picture."""
        Category = self.env['product.public.category']
        empty = Category.create({'name': 'Empty Family'})
        pictured = Category.create({'name': 'Pictured Family', 'image_1920': PNG})
        self.env['product.template'].create({
            'name': 'Pictured Lamp', 'list_price': 90, 'is_published': True,
            'public_categ_ids': [Command.set(pictured.ids)]})
        plain = Category.create({'name': 'Plain Family'})
        plain_product = self.env['product.template'].create({
            'name': 'Plain Lamp', 'list_price': 0, 'is_published': True,
            'public_categ_ids': [Command.set(plain.ids)]})
        names = {c['name']: c for c in self.website._arqora_collections(
            limit=50)}
        self.assertNotIn(empty.name, names)
        self.assertIn(
            'product.public.category/{}/image_1024'.format(pictured.id),
            names['Pictured Family']['image'])
        self.assertEqual(
            names['Plain Family']['image'],
            '/web/image/product.template/{}/image_1024'.format(
                plain_product.id))
        self.assertEqual(names['Plain Family']['from_price'], '')
        self.assertEqual(len(self.website._arqora_collections(limit=1)), 1)
