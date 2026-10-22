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
from base64 import b64decode

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes
from odoo.tools.image import image_data_uri

# Minimal 1x1 PNG image for testing. Binary fields accept BinaryValue objects.
TEST_IMAGE = BinaryBytes(b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
))


@tagged('post_install', '-at_install')
class TestPosConfigLogo(TransactionCase):
    """Test suite for Point of Sale logo configuration and receipt data generation."""

    @classmethod
    def setUpClass(cls):
        """Set up POS config and order for logo tests."""  # pylint: disable=invalid-name
        super().setUpClass()
        cls.company = cls.env.user.company_id
        if not cls.company.logo:
            cls.company.logo = TEST_IMAGE

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config Logo',
            'company_id': cls.company.id,
            'logo_option': 'pos',
            'image': TEST_IMAGE,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })
        cls.pos_order = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })

    def test_pos_config_logo_fields_default_and_write(self):
        """Test default values and updating logo fields on pos.config."""
        config = self.env['pos.config'].create({
            'name': 'Default POS Logo Test',
        })
        self.assertEqual(config.logo_option, 'pos', "Default logo_option should be 'pos'")
        self.assertFalse(config.image, "Default image should be False")

        config.write({
            'logo_option': 'company',
            'image': TEST_IMAGE,
        })
        self.assertEqual(config.logo_option, 'company')
        self.assertEqual(config.image, TEST_IMAGE)

        config.write({
            'logo_option': 'both',
        })
        self.assertEqual(config.logo_option, 'both')

    def test_order_receipt_data_pos_logo_only(self):
        """Test receipt data generation when logo_option is 'pos' with a POS image."""
        self.pos_config.write({
            'logo_option': 'pos',
            'image': TEST_IMAGE,
        })
        data = self.pos_order.order_receipt_generate_data()
        image_data = data.get('image', {})

        self.assertEqual(image_data.get('logo_option'), 'pos')
        self.assertTrue(image_data.get('logo'))
        self.assertEqual(image_data.get('logo'), image_data_uri(TEST_IMAGE))
        self.assertFalse(image_data.get('pos_logo'))
        self.assertFalse(image_data.get('company_logo'))

    def test_order_receipt_data_pos_logo_fallback_company(self):
        """Test receipt data generation when logo_option is 'pos' without a POS image."""
        self.pos_config.write({
            'logo_option': 'pos',
            'image': False,
        })
        data = self.pos_order.order_receipt_generate_data()
        image_data = data.get('image', {})

        self.assertEqual(image_data.get('logo_option'), 'pos')
        self.assertTrue(image_data.get('logo'))
        self.assertEqual(image_data.get('logo'), image_data_uri(self.company.logo))
        self.assertFalse(image_data.get('pos_logo'))
        self.assertFalse(image_data.get('company_logo'))

    def test_order_receipt_data_company_logo_only(self):
        """Test receipt data generation when logo_option is 'company'."""
        self.pos_config.write({
            'logo_option': 'company',
            'image': TEST_IMAGE,
        })
        data = self.pos_order.order_receipt_generate_data()
        image_data = data.get('image', {})

        self.assertEqual(image_data.get('logo_option'), 'company')
        self.assertTrue(image_data.get('logo'))
        self.assertEqual(image_data.get('logo'), image_data_uri(self.company.logo))
        self.assertFalse(image_data.get('pos_logo'))
        self.assertFalse(image_data.get('company_logo'))

    def test_order_receipt_data_both_logos(self):
        """Test receipt data generation when logo_option is 'both'."""
        self.pos_config.write({
            'logo_option': 'both',
            'image': TEST_IMAGE,
        })
        data = self.pos_order.order_receipt_generate_data()
        image_data = data.get('image', {})

        self.assertEqual(image_data.get('logo_option'), 'both')
        self.assertEqual(image_data.get('pos_logo'), image_data_uri(TEST_IMAGE))
        self.assertEqual(image_data.get('company_logo'), image_data_uri(self.company.logo))
        self.assertFalse(image_data.get('logo'))
