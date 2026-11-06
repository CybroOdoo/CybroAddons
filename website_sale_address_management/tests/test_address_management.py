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

from unittest.mock import patch

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_address_management.controllers.\
    website_sale_address_management import CustomWebsiteSale
from odoo.tests import TransactionCase, tagged

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
        cls.website = cls.env.ref('website.default_website')

    def _clear(self):
        for prefix in ('billing', 'shipping'):
            for key in ('phone', 'street', 'street2', 'city', 'zip_code'):
                self.Config.set_param(
                    '%sis_%s_%s' % (PREFIX, prefix, key), False)
                self.Config.set_param(
                    '%sis_%s_%s_is_required' % (PREFIX, prefix, key), False)

    def test_01_mandatory_fields_logic(self):
        """Required flags are stored as 'True' and removed when unset."""
        key = PREFIX + 'is_billing_street_is_required'
        self.Config.set_param(key, True)
        self.assertEqual(self.Config.get_param(key), 'True')
        # set_param(False) deletes the parameter, get_param returns False.
        self.Config.set_param(key, False)
        self.assertFalse(self.Config.get_param(key))

    def test_02_default_country_application(self):
        for prefix, country in (('billing', self.country_in),
                                ('shipping', self.country_us)):
            key = PREFIX + prefix + '_country'
            self.Config.set_param(key, country.id)
            self.assertEqual(int(self.Config.get_param(key)), country.id)

    def test_03_field_visibility_toggles(self):
        key = PREFIX + 'is_billing_phone'
        self.Config.set_param(key, True)
        self.assertEqual(self.Config.get_param(key), 'True')
        self.Config.set_param(key, False)
        self.assertFalse(self.Config.get_param(key))

    def test_04_field_config_helper(self):
        """Only toggled-on fields are visible; required needs visible."""
        self._clear()
        self.Config.set_param(PREFIX + 'billing_country', False)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertFalse(any(cfg[f]['visible'] for f in
                             ('phone', 'street', 'street2', 'city', 'zip')))
        self.assertFalse(cfg['default_country_id'])

        self.Config.set_param(PREFIX + 'is_billing_phone', True)
        self.Config.set_param(PREFIX + 'is_billing_phone_is_required', True)
        self.Config.set_param(PREFIX + 'is_billing_street_is_required', True)
        self.Config.set_param(PREFIX + 'billing_country', self.country_in.id)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertTrue(cfg['phone'] == {'visible': True, 'required': True})
        # required but hidden -> not required
        self.assertEqual(cfg['street'], {'visible': False, 'required': False})
        self.assertEqual(cfg['default_country_id'], self.country_in.id)
        # shipping is independent
        cfg = self.Settings.get_address_field_config('delivery')
        self.assertFalse(cfg['phone']['visible'])

        self.Config.set_param(PREFIX + 'is_shipping_zip_code', True)
        self.Config.set_param(PREFIX + 'shipping_country', self.country_us.id)
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
                vals['is_%s_%s' % (prefix, name)] = False
                vals['is_%s_%s_is_required' % (prefix, name)] = True
        settings = self.Settings.new(vals)
        settings._onchange_fields()
        for prefix in ('billing', 'shipping'):
            for name in names:
                self.assertFalse(
                    settings['is_%s_%s_is_required' % (prefix, name)])
        # fields left on keep their required flag
        settings = self.Settings.new({
            'is_billing_phone': True, 'is_billing_phone_is_required': True})
        settings._onchange_fields()
        self.assertTrue(settings.is_billing_phone_is_required)

    def test_06_controller_mandatory_fields(self):
        self._clear()
        controller = CustomWebsiteSale()
        with MockRequest(self.env, website=self.website):
            for getter, prefix in (
                (controller._get_mandatory_billing_address_fields,
                 'billing'),
                (controller._get_mandatory_delivery_address_fields,
                 'shipping'),
            ):
                fields = getter(self.country_in)
                self.assertFalse(fields & {'phone', 'street', 'city', 'zip'})
                self.Config.set_param(PREFIX + 'is_%s_street' % prefix, True)
                self.Config.set_param(
                    PREFIX + 'is_%s_street_is_required' % prefix, True)
                self.assertIn('street', getter(self.country_in))

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
            self.Config.set_param(PREFIX + 'is_billing_city', True)
            self.Config.set_param(PREFIX + 'is_billing_city_is_required', True)
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
            self.Config.set_param(PREFIX + 'is_billing_city', True)
            self.Config.set_param(PREFIX + 'is_billing_city_is_required', True)
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
        self.Config.set_param(PREFIX + 'billing_country', False)
        self.Config.set_param(PREFIX + 'shipping_country', False)
        controller = CustomWebsiteSale()
        customer = self.env['res.partner'].create({'name': 'Cart Customer'})
        order = self.env['sale.order'].create({
            'partner_id': customer.id,
            'website_id': self.website.id,
        })
        new_address = self.env['res.partner']
        values = self._prepare_form_values(controller, new_address, order)
        self.assertFalse(values['country'])

        self.Config.set_param(PREFIX + 'billing_country', self.country_in.id)
        values = self._prepare_form_values(controller, new_address, order)
        self.assertEqual(values['country'], self.country_in)
        self.assertEqual(values['country_states'], self.country_in.state_ids)

        # The delivery address uses its own default country.
        self.Config.set_param(PREFIX + 'shipping_country', self.country_us.id)
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            values = controller._prepare_address_form_values(
                new_address, address_type='delivery', order_sudo=order)
        self.assertEqual(values['country'], self.country_us)

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
            'website_sale_address_management.address_form_fields')
        self.assertTrue(view.active)
        self.assertEqual(
            view.inherit_id, self.env.ref('website_sale.address_form_fields'))
        for fname in ('phone', 'street', 'street2', 'city', 'zip'):
            self.assertIn("addr_cfg['%s']['visible']" % fname, view.arch_db)
