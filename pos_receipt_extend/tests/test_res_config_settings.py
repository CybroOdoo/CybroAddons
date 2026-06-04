# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config Settings',
        })

    def _get_settings(self):
        return self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })

    # --- Related field reads through to pos.config ---

    def test_customer_details_related_read(self):
        self.pos_config.customer_details = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_details)

    def test_customer_name_related_read(self):
        self.pos_config.customer_name = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_name)

    def test_customer_address_related_read(self):
        self.pos_config.customer_address = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_address)

    def test_customer_mobile_related_read(self):
        self.pos_config.customer_mobile = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_mobile)

    def test_customer_phone_related_read(self):
        self.pos_config.customer_phone = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_phone)

    def test_customer_email_related_read(self):
        self.pos_config.customer_email = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_email)

    def test_customer_vat_related_read(self):
        self.pos_config.customer_vat = True
        settings = self._get_settings()
        self.assertTrue(settings.customer_vat)

    # --- Related field writes back to pos.config ---

    def test_customer_details_related_write(self):
        settings = self._get_settings()
        settings.customer_details = True
        self.assertTrue(self.pos_config.customer_details)

    def test_customer_name_related_write(self):
        settings = self._get_settings()
        settings.customer_name = True
        self.assertTrue(self.pos_config.customer_name)

    def test_customer_address_related_write(self):
        settings = self._get_settings()
        settings.customer_address = True
        self.assertTrue(self.pos_config.customer_address)

    def test_customer_mobile_related_write(self):
        settings = self._get_settings()
        settings.customer_mobile = True
        self.assertTrue(self.pos_config.customer_mobile)

    def test_customer_phone_related_write(self):
        settings = self._get_settings()
        settings.customer_phone = True
        self.assertTrue(self.pos_config.customer_phone)

    def test_customer_email_related_write(self):
        settings = self._get_settings()
        settings.customer_email = True
        self.assertTrue(self.pos_config.customer_email)

    def test_customer_vat_related_write(self):
        settings = self._get_settings()
        settings.customer_vat = True
        self.assertTrue(self.pos_config.customer_vat)

    # --- Toggling off ---

    def test_customer_details_toggle_off(self):
        self.pos_config.customer_details = True
        settings = self._get_settings()
        settings.customer_details = False
        self.assertFalse(self.pos_config.customer_details)

    def test_all_fields_toggle_off(self):
        self.pos_config.write({
            'customer_details': True,
            'customer_name': True,
            'customer_address': True,
            'customer_mobile': True,
            'customer_phone': True,
            'customer_email': True,
            'customer_vat': True,
        })
        settings = self._get_settings()
        settings.write({
            'customer_details': False,
            'customer_name': False,
            'customer_address': False,
            'customer_mobile': False,
            'customer_phone': False,
            'customer_email': False,
            'customer_vat': False,
        })
        config = self.pos_config
        self.assertFalse(config.customer_details)
        self.assertFalse(config.customer_name)
        self.assertFalse(config.customer_address)
        self.assertFalse(config.customer_mobile)
        self.assertFalse(config.customer_phone)
        self.assertFalse(config.customer_email)
        self.assertFalse(config.customer_vat)