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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPosRefundPassword(common.TransactionCase):
    """Test cases for POS refund password security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Shop Refund',
            'payment_method_ids': [],
        })
        cls.param_model = cls.env['ir.config_parameter'].sudo()
        cls.cashier_user = cls.env['res.users'].create({
            'name': 'POS Cashier Test',
            'login': 'pos_cashier_test_user',
            'email': 'cashier_test@example.com',
            'group_ids': [
                (4, cls.env.ref('base.group_user').id),
                (4, cls.env.ref('point_of_sale.group_pos_user').id),
            ],
        })

    def setUp(self):
        super().setUp()
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '',
        )

    def tearDown(self):
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '',
        )
        super().tearDown()

    def test_default_state(self):
        """Test default config without refund password."""
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '',
        )
        self.pos_config.refund_security = False
        self.pos_config._compute_has_refund_password()
        self.assertFalse(self.pos_config.has_refund_password)
        self.assertTrue(self.pos_config.verify_refund_password('any_input'))

    def test_pos_specific_password(self):
        """Test POS-specific refund password with leading zeros."""
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '',
        )
        self.pos_config.refund_security = '0123'
        self.pos_config._compute_has_refund_password()
        self.assertTrue(self.pos_config.has_refund_password)
        self.assertTrue(self.pos_config.verify_refund_password('0123'))
        self.assertFalse(self.pos_config.verify_refund_password('123'))
        self.assertFalse(self.pos_config.verify_refund_password('wrong'))
        self.assertFalse(self.pos_config.verify_refund_password(''))
        self.assertFalse(self.pos_config.verify_refund_password(None))

    def test_global_password_override(self):
        """Test global refund password overrides POS-specific password."""
        self.pos_config.refund_security = '1111'
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '9999',
        )
        self.pos_config._compute_has_refund_password()
        self.assertTrue(self.pos_config.has_refund_password)
        self.assertTrue(self.pos_config.verify_refund_password('9999'))
        self.assertFalse(self.pos_config.verify_refund_password('1111'))
        self.assertFalse(self.pos_config.verify_refund_password('0000'))

    def test_global_password_with_leading_zeros(self):
        """Test global refund password preserves leading zeros."""
        self.pos_config.refund_security = False
        self.param_model.set_str(
            'pos_refund_password.global_refund_security', '0077',
        )
        self.pos_config._compute_has_refund_password()
        self.assertTrue(self.pos_config.has_refund_password)
        self.assertTrue(self.pos_config.verify_refund_password('0077'))
        self.assertFalse(self.pos_config.verify_refund_password('77'))

    def test_load_pos_data_read(self):
        """Test that has_refund_password is included in loaded POS data."""
        self.pos_config.refund_security = '4321'
        self.pos_config._compute_has_refund_password()
        data = self.env['pos.config']._load_pos_data_read(
            self.pos_config, self.pos_config,
        )
        self.assertTrue(data)
        self.assertIn('has_refund_password', data[0])
        self.assertTrue(data[0]['has_refund_password'])

    def test_res_config_settings_field(self):
        """Test setting global refund password via settings."""
        settings = self.env['res.config.settings'].create({
            'global_refund_security': '5555',
        })
        settings.set_values()
        param_val = self.param_model.get_str(
            'pos_refund_password.global_refund_security',
        )
        self.assertEqual(param_val, '5555')

    def test_cashier_access_without_manager_rights(self):
        """Test cashier without manager rights computes has_refund_password
        and reads POS data without raising an AccessError.
        """
        self.pos_config.refund_security = '8888'
        config_as_cashier = self.pos_config.with_user(self.cashier_user)

        # Computation must succeed without AccessError for cashier
        config_as_cashier._compute_has_refund_password()
        self.assertTrue(config_as_cashier.has_refund_password)

        # POS data loading must also succeed without AccessError for cashier
        data = self.env['pos.config'].with_user(
            self.cashier_user,
        )._load_pos_data_read(
            config_as_cashier, config_as_cashier,
        )
        self.assertTrue(data)
        self.assertTrue(data[0].get('has_refund_password'))

        # Password verification RPC must work for cashier
        self.assertTrue(config_as_cashier.verify_refund_password('8888'))
        self.assertFalse(config_as_cashier.verify_refund_password('wrong'))
