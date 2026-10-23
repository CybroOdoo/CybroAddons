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
from odoo.tests import HttpCase, TransactionCase, tagged

PARAM = 'delivery_date_ecommerce.is_delivery'


@tagged('post_install', '-at_install')
class TestDeliveryDateSettings(TransactionCase):
    """Test the 'Show delivery date' setting and the inherited views."""

    def _save_setting(self, value):
        """Save the 'Show delivery date' option as the settings screen does."""
        settings = self.env['res.config.settings'].create(
            {'is_delivery': value})
        settings.execute()

    def test_delivery_date_is_disabled_by_default(self):
        """The delivery date is not shown until the option is enabled."""
        self._save_setting(False)
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.is_delivery)

    def test_enable_saves_system_parameter(self):
        """Enabling the option stores a true value in the system parameter."""
        self._save_setting(True)
        self.assertTrue(
            self.env['ir.config_parameter'].sudo().get_bool(PARAM))

    def test_disable_clears_system_parameter(self):
        """Disabling the option stores a false value in the parameter."""
        self._save_setting(True)
        self._save_setting(False)
        self.assertFalse(
            self.env['ir.config_parameter'].sudo().get_bool(PARAM))

    def test_saved_setting_is_loaded(self):
        """The settings screen shows the value that was saved earlier."""
        self._save_setting(True)
        values = self.env['res.config.settings'].default_get(['is_delivery'])
        self.assertTrue(values['is_delivery'])

    def test_settings_view_contains_field(self):
        """The 'Show delivery date' field is part of the settings form."""
        arch = self.env['res.config.settings'].get_view(
            view_type='form')['arch']
        self.assertIn('is_delivery', arch)

    def test_templates_extend_website_sale_views(self):
        """Each template extends the expected eCommerce view and is active."""
        expected = {
            'delivery_date_ecommerce.ecommerce_delivery_date_template':
                'website_sale.product_image_and_ribbon',
            'delivery_date_ecommerce.ecommerce_delivery_date_product_template':
                'website_sale.cta_wrapper',
            'delivery_date_ecommerce.cart_delivery_date_template':
                'website_sale.cart_lines',
        }
        for xml_id, parent_xml_id in expected.items():
            view = self.env.ref(xml_id)
            self.assertTrue(view.active, xml_id)
            self.assertEqual(
                view.inherit_id, self.env.ref(parent_xml_id), xml_id)


@tagged('post_install', '-at_install')
class TestDeliveryDateWebsite(HttpCase):
    """Test the delivery date shown on the eCommerce pages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Delivery Date Test Product',
            'type': 'consu',
            'list_price': 10.0,
            'sale_ok': True,
            'is_published': True,
            'sale_delay': 5,
        })

    def _set_enabled(self, value):
        settings = self.env['res.config.settings'].create(
            {'is_delivery': value})
        settings.execute()

    def _get_product_page(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        return response.text

    def _get_shop_page(self):
        response = self.url_open('/shop?search=Delivery Date Test Product')
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_product_page_shows_delivery_time(self):
        """The product page shows the lead time when the option is on."""
        self._set_enabled(True)
        page = self._get_product_page()
        self.assertIn('show_delivery_date', page)
        self.assertIn('Delivery within', page)

    def test_shop_page_shows_delivery_time(self):
        """The product card in the shop shows the lead time."""
        self._set_enabled(True)
        page = self._get_shop_page()
        self.assertIn('show_delivery_date', page)

    def test_nothing_is_shown_when_option_is_disabled(self):
        """The shop and the product page hide the lead time when it is off."""
        self._set_enabled(False)
        self.assertNotIn('show_delivery_date', self._get_product_page())
        self.assertNotIn('show_delivery_date', self._get_shop_page())

    def test_nothing_is_shown_without_lead_time(self):
        """A product without a Customer Lead Time shows no delivery time."""
        self._set_enabled(True)
        self.product.sale_delay = 0
        self.assertNotIn('show_delivery_date', self._get_product_page())
        self.assertNotIn('show_delivery_date', self._get_shop_page())

    def _get_cart_page(self):
        """Open the cart page with one line of the test product in it."""
        website = self.env['website'].search([], limit=1)
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.public_partner').id,
            'website_id': website.id,
            'order_line': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'product_uom_qty': 1,
            })],
        })
        self.authenticate(None, None)
        self.update_session(sale_order_id=order.id)
        response = self.url_open('/shop/cart')
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_cart_page_shows_delivery_time(self):
        """The cart line shows the lead time when the option is on."""
        self._set_enabled(True)
        page = self._get_cart_page()
        self.assertIn('show_delivery_date', page)
        self.assertIn('Delivery within', page)

    def test_cart_page_hides_delivery_time_when_disabled(self):
        """The cart line hides the lead time when the option is off."""
        self._set_enabled(False)
        self.assertNotIn('show_delivery_date', self._get_cart_page())
