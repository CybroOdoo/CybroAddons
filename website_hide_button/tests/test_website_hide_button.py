# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from urllib.parse import urlparse

from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


class TestWebsiteHideButton(TransactionCase):
    """Cover the module's configuration and access-control behavior."""

    def setUp(self):
        super().setUp()
        self.config_parameter = self.env['ir.config_parameter'].sudo()

    def test_hide_price_onchange_enables_hide_cart(self):
        """Enabling hidden prices must also enable hidden cart controls."""
        settings = self.env['res.config.settings'].create({
            'hide_price': True,
            'hide_cart': False,
        })

        settings._onchange_hide_price()

        self.assertTrue(settings.hide_cart)

    def test_settings_store_and_read_values(self):
        """The two settings are stored as configuration parameters."""
        settings = self.env['res.config.settings'].create({
            'hide_price': True,
            'hide_cart': True,
        })
        settings.execute()

        self.assertEqual(
            self.config_parameter.get_str('website_hide_button.hide_price'),
            'True',
        )
        self.assertEqual(
            self.config_parameter.get_str('website_hide_button.hide_cart'),
            'True',
        )
        self.assertEqual(
            settings.get_smartsupp_details(),
            {'hide_price': 'True', 'hide_cart': 'True'},
        )


@tagged('post_install', '-at_install')
class TestWebsiteHideButtonController(HttpCase):
    """Exercise the /shop/payment route through real HTTP requests.

    Routed controller methods cannot be called directly in tests (they are
    wrapped by the routing layer and need a bound request), so the checks
    go through ``url_open``.
    """

    def _redirect_path(self, response):
        """Return the path of the redirect target of ``response``."""
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        return urlparse(response.headers['Location']).path

    def test_shop_payment_redirects_public_user(self):
        """A public visitor cannot open the payment page."""
        self.authenticate(None, None)
        response = self.url_open('/shop/payment', allow_redirects=False)
        self.assertEqual(self._redirect_path(response), '/')

    def test_shop_payment_allows_portal_user(self):
        """Portal users are not bounced to the home page."""
        self.env['res.users'].create({
            'name': 'Portal Hide Button',
            'login': 'portal_hide_button',
            'password': 'portal_hide_button',
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.authenticate('portal_hide_button', 'portal_hide_button')
        response = self.url_open('/shop/payment', allow_redirects=False)
        # Standard flow: with no cart Odoo redirects to the cart page, never '/'.
        if response.status_code in (301, 302, 303, 307, 308):
            self.assertNotEqual(self._redirect_path(response), '/')
        else:
            self.assertEqual(response.status_code, 200)