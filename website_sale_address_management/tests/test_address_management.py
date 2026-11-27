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
from unittest.mock import patch

from lxml import html as lxml_html

from odoo.fields import Command
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.models.website import CART_SESSION_CACHE_KEY
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon
from odoo.addons.website_sale_address_management.controllers.\
    website_sale_address_management import CustomWebsiteSale

PREFIX = 'website_sale_address_management.'


@tagged('post_install', '-at_install')
class TestWebsiteSaleAddressManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_in = cls.env.ref('base.in')
        cls.country_us = cls.env.ref('base.us')
        cls.Config = cls.env['ir.config_parameter'].sudo()
        cls.Settings = cls.env['res.config.settings']
        cls.website = (
            cls.env.ref('website.default_website', raise_if_not_found=False)
            or cls.env['website'].search([], limit=1)
            or cls.env['website'].create({
                'name': 'Test Website',
                'company_id': cls.env.company.id,
            })
        )

    def _set_param(self, key, value):
        if key.endswith('_country'):
            int_val = int(value) if value else None
            if hasattr(self.Config, 'set_int'):
                self.Config.set_int(key, int_val)
            else:
                self.Config.set_param(key, int_val or False)
            return
        if isinstance(value, bool):
            if hasattr(self.Config, 'set_bool'):
                self.Config.set_bool(key, value)
            else:
                self.Config.set_param(key, value)
        elif isinstance(value, int):
            if hasattr(self.Config, 'set_int'):
                self.Config.set_int(key, value)
            else:
                self.Config.set_param(key, value)
        elif value is None:
            if hasattr(self.Config, 'set_str'):
                self.Config.set_str(key, None)
            else:
                self.Config.set_param(key, False)
        else:
            if hasattr(self.Config, 'set_str'):
                self.Config.set_str(key, str(value))
            else:
                self.Config.set_param(key, value)

    def _get_param_bool(self, key):
        if hasattr(self.Config, 'get_bool'):
            return self.Config.get_bool(key)
        return self.Config.get_param(key) in ('True', 'true', '1', True)

    def _get_param_int(self, key):
        if hasattr(self.Config, 'get_int'):
            return self.Config.get_int(key)
        val = self.Config.get_param(key)
        return int(val) if (val and str(val).isdigit()) else 0

    def _clear(self):
        for prefix in ('billing', 'shipping'):
            for key in ('phone', 'street', 'street2', 'city', 'zip_code'):
                self._set_param(
                    f'{PREFIX}is_{prefix}_{key}', False)
                self._set_param(
                    f'{PREFIX}is_{prefix}_{key}_is_required', False)

    def test_01_mandatory_fields_logic(self):
        """Required flags are stored as 'True' and removed when unset."""
        key = PREFIX + 'is_billing_street_is_required'
        self._set_param(key, True)
        self.assertTrue(self._get_param_bool(key))
        # set_param(False) deletes the parameter, get_param returns False.
        self._set_param(key, False)
        self.assertFalse(self._get_param_bool(key))

    def test_02_default_country_application(self):
        for prefix, country in (('billing', self.country_in),
                                ('shipping', self.country_us)):
            key = PREFIX + prefix + '_country'
            self._set_param(key, country.id)
            self.assertEqual(self._get_param_int(key), country.id)

    def test_03_field_visibility_toggles(self):
        key = PREFIX + 'is_billing_phone'
        self._set_param(key, True)
        self.assertTrue(self._get_param_bool(key))
        self._set_param(key, False)
        self.assertFalse(self._get_param_bool(key))

    def test_04_field_config_helper(self):
        """Only toggled-on fields are visible; required needs visible."""
        self._clear()
        self._set_param(PREFIX + 'billing_country', None)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertFalse(any(cfg[f]['visible'] for f in
                             ('phone', 'street', 'street2', 'city', 'zip')))
        self.assertFalse(cfg['default_country_id'])

        self._set_param(PREFIX + 'is_billing_phone', True)
        self._set_param(PREFIX + 'is_billing_phone_is_required', True)
        self._set_param(PREFIX + 'is_billing_street_is_required', True)
        self._set_param(PREFIX + 'billing_country', self.country_in.id)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertTrue(cfg['phone'] == {'visible': True, 'required': True})
        # required but hidden -> not required
        self.assertEqual(cfg['street'], {'visible': False, 'required': False})
        self.assertEqual(cfg['default_country_id'], self.country_in.id)
        # shipping is independent
        cfg = self.Settings.get_address_field_config('delivery')
        self.assertFalse(cfg['phone']['visible'])

        self._set_param(PREFIX + 'is_shipping_zip_code', True)
        self._set_param(PREFIX + 'shipping_country', self.country_us.id)
        cfg = self.Settings.get_address_field_config('shipping')
        self.assertTrue(cfg['zip']['visible'])
        self.assertFalse(cfg['zip']['required'])
        self.assertEqual(cfg['default_country_id'], self.country_us.id)

    def test_05_onchange_resets_required(self):
        """Switching a field off switches its 'required' flag off."""
        names = ('phone', 'street', 'city', 'zip_code')
        vals = {}
        for prefix in ('billing', 'shipping'):
            for name in names:
                vals[f'is_{prefix}_{name}'] = False
                vals[f'is_{prefix}_{name}_is_required'] = True
        settings = self.Settings.new(vals)
        settings._onchange_fields()
        for prefix in ('billing', 'shipping'):
            for name in names:
                self.assertFalse(
                    settings[f'is_{prefix}_{name}_is_required'])
        # fields left on keep their required flag
        settings = self.Settings.new({
            'is_billing_phone': True, 'is_billing_phone_is_required': True})
        settings._onchange_fields()
        self.assertTrue(settings.is_billing_phone_is_required)

    def test_06_required_address_fields(self):
        """Partner required address fields follow billing/delivery configuration."""
        self._clear()
        partner = self.env['res.partner']
        with MockRequest(self.env, website=self.website):
            for address_type, prefix in (
                ('billing', 'billing'),
                ('delivery', 'shipping'),
            ):
                fields = partner._get_required_address_fields(
                    address_type, self.country_in,
                )
                self.assertFalse(fields & {'phone', 'street', 'city', 'zip'})
                self._set_param(f'{PREFIX}is_{prefix}_street', True)
                self._set_param(
                    f'{PREFIX}is_{prefix}_street_is_required', True,
                )
                self.assertIn(
                    'street',
                    partner._get_required_address_fields(
                        address_type, self.country_in,
                    ),
                )
            # use_delivery_as_billing merges billing and delivery requirements
            combined = partner._get_required_address_fields(
                'delivery', self.country_in, use_delivery_as_billing=True,
            )
            self.assertIn('street', combined)

    def test_07_controller_validation(self):
        self._clear()
        controller = CustomWebsiteSale()
        partner = self.env['res.partner']
        values = {'name': 'Test', 'country_id': self.country_in.id}
        with MockRequest(self.env, website=self.website):
            _inv, missing, _msg = controller._validate_address_values(
                values, partner, 'billing', False, 'name,street,city')
            # phone, street, city and zip are not configured as required
            # (email and state_id stay mandatory in core)
            self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})
            self._set_param(PREFIX + 'is_billing_city', True)
            self._set_param(PREFIX + 'is_billing_city_is_required', True)
            _inv, missing, msgs = controller._validate_address_values(
                values, partner, 'billing', False, 'name')
            self.assertIn('city', missing)
            self.assertTrue(msgs)
            # delivery used as billing: required on either side applies
            _inv, missing, _msg = controller._validate_address_values(
                values, partner, 'delivery', True, 'name')
            self.assertIn('city', missing)
            # invalid email is reported
            invalid, _missing, _msg = controller._validate_address_values(
                dict(values, email='bad'), partner, 'billing', False, '')
            self.assertIn('email', invalid)

    def test_08_validation_accepts_core_kwargs(self):
        """Extra core arguments are forwarded to the core validation."""
        self._clear()
        controller = CustomWebsiteSale()
        values = {'name': 'Test', 'country_id': self.country_in.id}
        with MockRequest(self.env, website=self.website):
            invalid, missing, _msg = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name',
                is_main_address=True)
        self.assertFalse(invalid)
        self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})

    def test_09_partial_address_keeps_optional_fields_optional(self):
        """Core asks for the whole address once a part of it is given, but
        the fields that are not configured as required stay optional."""
        self._clear()
        controller = CustomWebsiteSale()
        values = {
            'name': 'Test',
            'country_id': self.country_in.id,
            'street': 'MG Road',
        }
        with MockRequest(self.env, website=self.website):
            _inv, missing, _msg = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name')
            self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})
            self._set_param(PREFIX + 'is_billing_city', True)
            self._set_param(PREFIX + 'is_billing_city_is_required', True)
            _inv, missing, msgs = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name')
            self.assertIn('city', missing)
            self.assertTrue(msgs)

    def _prepare_form_values(self, controller, partner, order):
        """Return the address form values, without any country coming from
        the current user."""
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            return controller._prepare_address_form_values(
                partner, address_type='billing', order_sudo=order)

    def test_10_default_country_in_address_form(self):
        """The configured default country is preselected on a new address
        of the cart, and does not replace the country of an address."""
        self._clear()
        self._set_param(PREFIX + 'billing_country', None)
        self._set_param(PREFIX + 'shipping_country', None)
        controller = CustomWebsiteSale()
        customer = self.env['res.partner'].create({'name': 'Cart Customer'})
        order = self.env['sale.order'].create({
            'partner_id': customer.id,
            'website_id': self.website.id,
        })
        new_address = self.env['res.partner']
        values = self._prepare_form_values(controller, new_address, order)
        self.assertFalse(values['country'])

        self._set_param(PREFIX + 'billing_country', self.country_in.id)
        values = self._prepare_form_values(controller, new_address, order)
        self.assertEqual(values['country'], self.country_in)
        self.assertEqual(values['states'], self.country_in.state_ids)
        self.assertEqual(
            values['zip_applicability'], self.country_in.zip_applicability,
        )
        self.assertEqual(
            values['zip_before_city'], self.country_in._is_zip_before_city(),
        )
        self.assertEqual(values['vat_label'], self.country_in._get_vat_label())
        self.assertEqual(
            values['required_fields'],
            self.env['res.partner']._get_required_address_fields(
                'billing', self.country_in, order_sudo=order,
            ),
        )

        # Delivery stays unset when only billing_country is configured.
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            delivery_values = controller._prepare_address_form_values(
                new_address, address_type='delivery', order_sudo=order,
            )
        self.assertFalse(delivery_values['country'])

        # Overriding a customer's country also updates country-dependent keys.
        country_be = self.env.ref('base.be')
        customer.country_id = self.country_us
        self._set_param(PREFIX + 'billing_country', country_be.id)
        be_values = self._prepare_form_values(controller, new_address, order)
        self.assertEqual(be_values['country'], country_be)
        self.assertNotIn('state_id', be_values['required_fields'])
        self.assertEqual(be_values['zip_before_city'], country_be._is_zip_before_city())
        self.assertEqual(be_values['vat_label'], country_be._get_vat_label())

        # The delivery address uses its own default country.
        self._set_param(PREFIX + 'shipping_country', self.country_us.id)
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            values = controller._prepare_address_form_values(
                new_address, address_type='delivery', order_sudo=order)
        self.assertEqual(values['country'], self.country_us)
        self.assertIn('state_id', values['required_fields'])

        # An existing address keeps its own country.
        existing = self.env['res.partner'].create({
            'name': 'Existing Address',
            'parent_id': customer.id,
            'type': 'delivery',
            'country_id': self.country_us.id,
        })
        values = self._prepare_form_values(controller, existing, order)
        self.assertEqual(values['country'], self.country_us)

    def test_11_address_form_template_extension(self):
        """The module extends the core address fields template instead of
        replacing the address form."""
        view = self.env.ref(
            'website_sale_address_management.'
            'address_form_fields_inherit_website_sale_address_management',
        )
        self.assertTrue(view.active)
        self.assertEqual(
            view.inherit_id, self.env.ref('website_sale.address_form_fields'))
        for fname in ('phone', 'street', 'street2', 'city', 'zip'):
            self.assertIn(f"addr_cfg['{fname}']['visible']", view.arch_db)

    def test_12_partner_mandatory_fields(self):
        """res.partner mandatory fields reflect the module configuration."""
        self._clear()
        partner = self.env['res.partner']
        # Initially none of the managed fields are required
        fields_billing = partner._get_mandatory_billing_address_fields(self.country_in)
        self.assertFalse(fields_billing & {'phone', 'street', 'city', 'zip'})

        self._set_param(PREFIX + 'is_billing_phone', True)
        self._set_param(PREFIX + 'is_billing_phone_is_required', True)
        self._set_param(PREFIX + 'is_shipping_city', True)
        self._set_param(PREFIX + 'is_shipping_city_is_required', True)

        fields_billing = partner._get_mandatory_billing_address_fields(self.country_in)
        self.assertIn('phone', fields_billing)
        self.assertNotIn('city', fields_billing)

        fields_shipping = partner._get_mandatory_delivery_address_fields(self.country_in)
        self.assertIn('city', fields_shipping)
        self.assertNotIn('phone', fields_shipping)

    def test_13_address_template_buttons(self):
        """The address template adds Save address and Discard buttons."""
        view = self.env.ref(
            'website_sale_address_management.'
            'address_inherit_website_sale_address_management',
        )
        self.assertTrue(view.active)
        self.assertEqual(
            view.inherit_id, self.env.ref('website_sale.address'))
        self.assertIn('save_address', view.arch_db)
        self.assertIn('Discard', view.arch_db)
        self.assertIn('discard_url', view.arch_db)

    def test_14_res_config_settings_save_and_load(self):
        """Saving res.config.settings persists values and reloads via default_get."""
        config_env = self.Settings.sudo().with_company(self.website.company_id)
        settings = config_env.create({
            'is_billing_phone': True,
            'is_billing_phone_is_required': True,
            'is_billing_street': False,
            'is_billing_street_is_required': False,
            'is_billing_street2': False,
            'is_billing_city': True,
            'is_billing_city_is_required': True,
            'is_billing_zip_code': True,
            'is_billing_zip_code_is_required': False,
            'billing_country_id': self.country_in.id,
            'is_shipping_phone': False,
            'is_shipping_phone_is_required': False,
            'is_shipping_street': True,
            'is_shipping_street_is_required': True,
            'is_shipping_street2': False,
            'is_shipping_city': False,
            'is_shipping_city_is_required': False,
            'is_shipping_zip_code': True,
            'is_shipping_zip_code_is_required': True,
            'shipping_country_id': self.country_us.id,
        })
        settings.execute()

        loaded = config_env.default_get([
            'is_billing_phone',
            'is_billing_phone_is_required',
            'is_billing_street',
            'is_billing_street2',
            'is_billing_city_is_required',
            'billing_country_id',
            'is_shipping_street',
            'is_shipping_street_is_required',
            'is_shipping_zip_code_is_required',
            'shipping_country_id',
        ])
        self.assertTrue(loaded['is_billing_phone'])
        self.assertTrue(loaded['is_billing_phone_is_required'])
        self.assertFalse(loaded['is_billing_street'])
        self.assertFalse(loaded['is_billing_street2'])
        self.assertTrue(loaded['is_billing_city_is_required'])
        self.assertEqual(loaded['billing_country_id'], self.country_in.id)
        self.assertTrue(loaded['is_shipping_street'])
        self.assertTrue(loaded['is_shipping_street_is_required'])
        self.assertTrue(loaded['is_shipping_zip_code_is_required'])
        self.assertEqual(loaded['shipping_country_id'], self.country_us.id)

        billing_cfg = self.Settings.get_address_field_config('billing')
        self.assertEqual(billing_cfg['street'], {'visible': False, 'required': False})
        self.assertEqual(billing_cfg['phone'], {'visible': True, 'required': True})
        self.assertEqual(billing_cfg['default_country_id'], self.country_in.id)

        # Clearing a Many2one country parameter stores undefined without errors.
        config_env.create({'billing_country_id': False}).execute()
        cleared = config_env.default_get(['billing_country_id'])
        self.assertFalse(cleared['billing_country_id'])
        self.assertFalse(
            self.Settings.get_address_field_config('billing')['default_country_id'],
        )


@tagged('post_install', '-at_install')
class TestWebsiteSaleAddressManagementHttp(WebsiteSaleCommon, HttpCase):
    """HTTP route tests for /shop/address and /shop/address/submit."""

    def _set_address_settings(self, vals):
        config_env = self.env['res.config.settings'].sudo().with_company(
            self.website.company_id,
        )
        config_env.create(vals).execute()

    def test_shop_address_get_and_submit(self):
        """Checkout address form hides disabled fields, preselects country, and submits."""
        self.website.sudo().account_on_checkout = 'optional'
        self._set_address_settings({
            'is_billing_phone': True,
            'is_billing_phone_is_required': False,
            'is_billing_street': False,
            'is_billing_street_is_required': False,
            'is_billing_street2': False,
            'is_billing_city': True,
            'is_billing_city_is_required': False,
            'is_billing_zip_code': True,
            'is_billing_zip_code_is_required': False,
            'billing_country_id': self.country_us.id,
        })

        anon_cart = self.env['sale.order'].create({
            'partner_id': self.public_partner.id,
            'website_id': self.website.id,
            'order_line': [
                Command.create({'product_id': self.product.id, 'product_uom_qty': 1.0}),
            ],
        })
        self.authenticate(None, None)
        self.update_session(**{CART_SESSION_CACHE_KEY: anon_cart.id})

        get_res = self.url_open('/shop/address?address_type=billing')
        self.assertEqual(get_res.status_code, 200)
        root = lxml_html.fromstring(get_res.content)
        self.assertFalse(root.xpath('//form[@name="address_form"]//input[@name="street"]'))
        self.assertFalse(root.xpath('//form[@name="address_form"]//input[@name="street2"]'))
        self.assertTrue(root.xpath('//form[@name="address_form"]//input[@name="phone"]'))
        self.assertTrue(root.xpath('//form[@name="address_form"]//input[@name="city"]'))
        self.assertTrue(root.xpath('//form[@name="address_form"]//input[@name="zip"]'))
        selected_country = root.xpath(
            '//form[@name="address_form"]//select[@name="country_id"]/option[@selected]/@value',
        )
        self.assertEqual(selected_country, [str(self.country_us.id)])

        csrf_token = root.xpath(
            '//form[@name="address_form"]//input[@name="csrf_token"]/@value',
        )[0]
        base_payload = {
            'csrf_token': csrf_token,
            'name': 'HTTP Checkout Customer',
            'email': 'http.customer@example.com',
            'country_id': str(self.country_us.id),
            'state_id': str(self.country_us_state_id),
            'address_type': 'billing',
            'use_delivery_as_billing': 'False',
            'required_fields': 'name,email',
            'phone': '',
            'city': '',
            'zip': '',
        }

        # Enabling required city fails validation when city is omitted.
        self._set_address_settings({'is_billing_city_is_required': True})
        err_res = self.url_open('/shop/address/submit', data=base_payload)
        self.assertEqual(err_res.status_code, 200)
        err_data = err_res.json()
        self.assertIn('city', err_data.get('invalid_fields', []))
        self.assertTrue(err_data.get('messages'))

        # With city optional and street hidden, submission succeeds without street/zip/phone.
        self._set_address_settings({'is_billing_city_is_required': False})
        ok_res = self.url_open('/shop/address/submit', data=base_payload)
        self.assertEqual(ok_res.status_code, 200)
        ok_data = ok_res.json()
        self.assertTrue(ok_data.get('redirectUrl'))
        self.assertFalse(ok_data.get('invalid_fields'))
