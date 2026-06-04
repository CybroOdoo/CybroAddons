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
class TestPosConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS',
        })

    # --- Field defaults ---

    def test_customer_details_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Test'})
        self.assertFalse(config.customer_details)

    def test_customer_name_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Name'})
        self.assertFalse(config.customer_name)

    def test_customer_address_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Addr'})
        self.assertFalse(config.customer_address)

    def test_customer_mobile_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Mobile'})
        self.assertFalse(config.customer_mobile)

    def test_customer_phone_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Phone'})
        self.assertFalse(config.customer_phone)

    def test_customer_email_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default Email'})
        self.assertFalse(config.customer_email)

    def test_customer_vat_default_false(self):
        config = self.env['pos.config'].create({'name': 'POS Default VAT'})
        self.assertFalse(config.customer_vat)

    # --- Field write ---

    def test_set_all_customer_fields_true(self):
        self.pos_config.write({
            'customer_details': True,
            'customer_name': True,
            'customer_address': True,
            'customer_mobile': True,
            'customer_phone': True,
            'customer_email': True,
            'customer_vat': True,
        })
        self.assertTrue(self.pos_config.customer_details)
        self.assertTrue(self.pos_config.customer_name)
        self.assertTrue(self.pos_config.customer_address)
        self.assertTrue(self.pos_config.customer_mobile)
        self.assertTrue(self.pos_config.customer_phone)
        self.assertTrue(self.pos_config.customer_email)
        self.assertTrue(self.pos_config.customer_vat)

    # --- _load_pos_data_read: empty recordset ---

    def test_load_pos_data_read_empty_recordset(self):
        empty = self.env['pos.config']
        result = self.pos_config._load_pos_data_read(empty, self.pos_config)
        self.assertFalse(result)

    # --- _load_pos_data_read: customer_details=False ---
    # The base read already includes all model fields in the result.
    # When customer_details=False, our override does NOT inject sub-fields,
    # so the values in the result are just whatever the DB has (False by default).

    def test_load_pos_data_read_customer_details_false_subfields_not_overridden(self):
        """customer_details=False: sub-fields in result reflect DB values, not injected."""
        self.pos_config.write({
            'customer_details': False,
            'customer_name': False,
            'customer_address': False,
            'customer_mobile': False,
            'customer_phone': False,
            'customer_email': False,
            'customer_vat': False,
        })
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertTrue(result)
        record = result[0]
        # Values come straight from DB read, not from our injection logic
        self.assertFalse(record.get('customer_name'))
        self.assertFalse(record.get('customer_address'))
        self.assertFalse(record.get('customer_mobile'))
        self.assertFalse(record.get('customer_phone'))
        self.assertFalse(record.get('customer_email'))
        self.assertFalse(record.get('customer_vat'))

    def test_load_pos_data_read_customer_details_false_returns_result(self):
        """customer_details=False: method still returns the read_records list."""
        self.pos_config.write({'customer_details': False})
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    # --- _load_pos_data_read: customer_details=True, sub-fields injected ---

    def test_load_pos_data_read_injects_false_values(self):
        """customer_details=True but sub-fields False: injected values are False."""
        self.pos_config.write({
            'customer_details': True,
            'customer_name': False,
            'customer_address': False,
            'customer_mobile': False,
            'customer_phone': False,
            'customer_email': False,
            'customer_vat': False,
        })
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertTrue(result)
        record = result[0]
        self.assertFalse(record['customer_name'])
        self.assertFalse(record['customer_address'])
        self.assertFalse(record['customer_mobile'])
        self.assertFalse(record['customer_phone'])
        self.assertFalse(record['customer_email'])
        self.assertFalse(record['customer_vat'])

    def test_load_pos_data_read_injects_mixed_values(self):
        """customer_details=True: mixed True/False sub-fields injected correctly."""
        self.pos_config.write({
            'customer_details': True,
            'customer_name': True,
            'customer_address': False,
            'customer_mobile': True,
            'customer_phone': False,
            'customer_email': True,
            'customer_vat': False,
        })
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertTrue(result)
        record = result[0]
        config = self.pos_config
        self.assertEqual(record['customer_name'], config.customer_name)
        self.assertEqual(record['customer_address'], config.customer_address)
        self.assertEqual(record['customer_mobile'], config.customer_mobile)
        self.assertEqual(record['customer_phone'], config.customer_phone)
        self.assertEqual(record['customer_email'], config.customer_email)
        self.assertEqual(record['customer_vat'], config.customer_vat)

    def test_load_pos_data_read_values_match_config(self):
        """Injected values always equal the config field values."""
        self.pos_config.write({
            'customer_details': True,
            'customer_name': False,
            'customer_address': True,
            'customer_mobile': False,
            'customer_phone': True,
            'customer_email': False,
            'customer_vat': True,
        })
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertTrue(result)
        record = result[0]
        config = self.pos_config
        self.assertEqual(record['customer_name'], config.customer_name)
        self.assertEqual(record['customer_address'], config.customer_address)
        self.assertEqual(record['customer_mobile'], config.customer_mobile)
        self.assertEqual(record['customer_phone'], config.customer_phone)
        self.assertEqual(record['customer_email'], config.customer_email)
        self.assertEqual(record['customer_vat'], config.customer_vat)

    def test_load_pos_data_read_returns_list(self):
        """Return type is always a list."""
        self.pos_config.write({'customer_details': True})
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertIsInstance(result, list)

    def test_load_pos_data_read_result_contains_id(self):
        """Result record contains the config id."""
        self.pos_config.write({'customer_details': True})
        result = self.pos_config._load_pos_data_read(
            self.pos_config, self.pos_config
        )
        self.assertTrue(result)
        self.assertEqual(result[0]['id'], self.pos_config.id)




