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
from urllib.parse import parse_qs, urlparse

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWhatsappProductInquiry(HttpCase):
    """Test the Inquire button and the WhatsApp redirection."""

    @classmethod
    def setUpClass(cls):
        """Configure the website company and create a published product."""
        super().setUpClass()
        cls.website = cls.env.ref('base.default_website')
        cls.company = cls.website.company_id
        cls.company.write({
            'whatsapp_number': '919876543210',
            'message': 'Hello, tell me more',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'WhatsApp Test Product',
            'sale_ok': True,
            'website_published': True,
        })

    def _inquire(self, product_id):
        """Open the inquiry route without following the redirection."""
        return self.url_open(f'/whatsapp/inquiry/{product_id}',
                             allow_redirects=False)

    def test_01_redirects_to_whatsapp(self):
        """The inquiry opens WhatsApp for the company number, with the
        message and the product link."""
        response = self._inquire(self.product.id)
        self.assertEqual(response.status_code, 303)
        location = urlparse(response.headers['Location'])
        self.assertEqual(f'{location.scheme}://{location.netloc}', 'https://wa.me')
        self.assertEqual(location.path, '/919876543210')
        text = parse_qs(location.query)['text'][0]
        self.assertTrue(text.startswith('Hello, tell me more\nProduct Url: '),
                        text)
        self.assertTrue(text.endswith(self.product.website_url), text)

    def test_02_without_message(self):
        """Without inquiry message, only the product link is sent."""
        self.company.message = False
        location = urlparse(self._inquire(self.product.id).headers['Location'])
        text = parse_qs(location.query)['text'][0]
        self.assertTrue(text.startswith('Product Url: '), text)

    def test_03_without_number(self):
        """Without WhatsApp number, the inquiry goes back to the product."""
        self.company.whatsapp_number = False
        response = self._inquire(self.product.id)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith(
            self.product.website_url), response.headers['Location'])

    def test_04_unavailable_products(self):
        """Unpublished and unknown products are not found."""
        unpublished = self.env['product.product'].create({
            'name': 'Hidden Product',
            'website_published': False,
        })
        for product_id in (unpublished.id, 999999999):
            with self.subTest(product_id=product_id):
                self.assertEqual(self._inquire(product_id).status_code, 404)

    def test_05_inquire_button_on_product_page(self):
        """The product page shows the Inquire button only when the website
        company has a WhatsApp number."""
        url = self.product.website_url
        html = self.url_open(url).text
        self.assertIn('id="whatsapp_inquiry_link"', html)
        self.assertIn(f'href="/whatsapp/inquiry/{self.product.id}"', html)
        self.company.whatsapp_number = False
        self.assertNotIn('id="whatsapp_inquiry_link"', self.url_open(url).text)
