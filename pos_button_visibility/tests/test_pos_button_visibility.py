# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.point_of_sale.tests.test_frontend import (
    TestPointOfSaleHttpCommon,
)


class TestPosButtonVisibility(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create pos buttons
        cls.pos_button_discount = cls.env['pos.buttons'].create(
            {'name': 'Discount'}
        )
        cls.pos_button_price = cls.env['pos.buttons'].create({'name': 'Price'})

        # Create a user and assign pos buttons
        cls.user = cls.env['res.users'].create({
            'name': 'Test POS User',
            'login': 'test_pos_user',
            'buttons_pos_ids': [
                (6, 0, [cls.pos_button_discount.id, cls.pos_button_price.id])
            ]
        })

        # _load_pos_data expects a dictionary containing a POS config.
        # The method only reads this value, so a mock data dict is enough.
        cls.mock_data = {
            'pos.config': {
                'data': [{'id': 1}]
            }
        }

    def test_pos_buttons_load_pos_data_fields(self):
        """Test the _load_pos_data_fields method in pos.buttons."""
        fields = self.env['pos.buttons']._load_pos_data_fields(1)
        self.assertEqual(fields, ['id', 'name'])

    def test_pos_buttons_load_pos_data_domain(self):
        """Test the _load_pos_data_domain method in pos.buttons."""
        domain = self.env['pos.buttons']._load_pos_data_domain(self.mock_data)
        self.assertEqual(domain, [])

    def test_pos_buttons_load_pos_data(self):
        """Test the _load_pos_data method in pos.buttons."""
        loaded_data = self.env['pos.buttons']._load_pos_data(self.mock_data)

        self.assertIn('data', loaded_data)
        self.assertIn('fields', loaded_data)
        self.assertEqual(loaded_data['fields'], ['id', 'name'])

        button_names = [record['name'] for record in loaded_data['data']]
        self.assertIn('Discount', button_names)
        self.assertIn('Price', button_names)

    def test_pos_session_load_pos_data_models(self):
        """Test the _load_pos_data_models method in pos.session."""
        models = self.env['pos.session']._load_pos_data_models(1)
        self.assertIn('pos.buttons', models)

    def test_res_users_load_pos_data_fields(self):
        """Test the _load_pos_data_fields method in res.users."""
        fields = self.env['res.users']._load_pos_data_fields(1)
        self.assertIn('buttons_pos_ids', fields)

    def test_refund_restricted_server_side(self):
        """A user restricted from refunds cannot sync refund lines."""
        refund_button = self.env.ref('pos_button_visibility.refund_pos_buttons')
        self.user.buttons_pos_ids = [(4, refund_button.id)]
        order = {'lines': [[0, 0, {'refunded_orderline_id': 1, 'qty': -1}]]}
        with self.assertRaises(UserError):
            self.env['pos.order'].with_user(self.user)._process_order(
                order, False)


@tagged('post_install', '-at_install')
class TestPosButtonVisibilityUi(TestPointOfSaleHttpCommon):

    def test_pos_button_visibility_tour(self):
        """Restricted buttons are disabled in the POS interface."""
        self.main_pos_config.manual_discount = True
        self.pos_user.buttons_pos_ids = [(6, 0, [
            self.env.ref('pos_button_visibility.pos_discount_buttons').id,
            self.env.ref('pos_button_visibility.pos_price_buttons').id,
            self.env.ref('pos_button_visibility.refund_pos_buttons').id,
        ])]
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour('PosButtonVisibilityTour', login='pos_user')
