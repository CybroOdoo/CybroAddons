# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase


class TestPosPayment(TransactionCase):
    """Test cases for the PosPayment model (pos.payment) extended fields
    payment_currency and currency_amount added by multi_currency_payment_in_pos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure a usable POS config exists
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config for Payment',
            })
        # Get a payment method (cash is always present)
        cls.payment_method = cls.env['pos.payment.method'].search(
            [('is_cash_count', '=', True)], limit=1
        )
        if not cls.payment_method:
            cls.payment_method = cls.env['pos.payment.method'].search([], limit=1)

    def _create_pos_order(self):
        """Helper: open a POS session and create a minimal POS order."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.user.id,
        })
        product = self.env['product.product'].search(
            [('available_in_pos', '=', True)], limit=1
        )
        if not product:
            product = self.env['product.product'].create({
                'name': 'Test POS Product',
                'type': 'consu',
                'available_in_pos': True,
                'list_price': 10.0,
            })
        order = self.env['pos.order'].create({
            'session_id': session.id,
            'lines': [(0, 0, {
                'product_id': product.id,
                'price_unit': 10.0,
                'qty': 1,
                'price_subtotal': 10.0,
                'price_subtotal_incl': 10.0,
            })],
            'amount_total': 10.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        return order

    def test_01_payment_currency_field_exists(self):
        """Verify that pos.payment model has the payment_currency field."""
        fields = self.env['pos.payment'].fields_get()
        self.assertIn(
            'payment_currency', fields,
            "pos.payment should have the custom 'payment_currency' field."
        )
  

    def test_02_currency_amount_field_exists(self):
        """Verify that pos.payment model has the currency_amount field."""
        fields = self.env['pos.payment'].fields_get()
        self.assertIn(
            'currency_amount', fields,
            "pos.payment should have the custom 'currency_amount' field."
        )
  

    def test_03_payment_currency_field_type(self):
        """Verify that payment_currency is a Char field."""
        field_info = self.env['pos.payment'].fields_get(['payment_currency'])
        self.assertEqual(
            field_info['payment_currency']['type'],
            'char',
            "payment_currency should be of type 'char'."
        )
  

    def test_04_currency_amount_field_type(self):
        """Verify that currency_amount is a Float field."""
        field_info = self.env['pos.payment'].fields_get(['currency_amount'])
        self.assertEqual(
            field_info['currency_amount']['type'],
            'float',
            "currency_amount should be of type 'float'."
        )
  

    def test_05_payment_currency_default_value(self):
        """Verify that payment_currency defaults to False/None when not set."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
        })
        self.assertFalse(
            payment.payment_currency,
            "payment_currency should be False/empty by default."
        )
  

    def test_06_currency_amount_default_value(self):
        """Verify that currency_amount defaults to 0.0 when not set."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
        })
        self.assertEqual(
            payment.currency_amount,
            0.0,
            "currency_amount should default to 0.0."
        )
  

    def test_07_write_payment_currency(self):
        """Verify that payment_currency can be written and read back."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
            'payment_currency': 'EUR',
        })
        self.assertEqual(
            payment.payment_currency,
            'EUR',
            "payment_currency should hold the written value 'EUR'."
        )
  

    def test_08_write_currency_amount(self):
        """Verify that currency_amount can be written and read back."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
            'currency_amount': 9.5,
        })
        self.assertAlmostEqual(
            payment.currency_amount,
            9.5,
            places=2,
            msg="currency_amount should hold the written value 9.5."
        )
  

    def test_09_update_payment_currency_after_create(self):
        """Verify that payment_currency can be updated after record creation."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
        })
        payment.payment_currency = 'USD'
        self.assertEqual(
            payment.payment_currency,
            'USD',
            "payment_currency should be updatable after creation."
        )
  

    def test_10_update_currency_amount_after_create(self):
        """Verify that currency_amount can be updated after record creation."""
        order = self._create_pos_order()
        if not self.payment_method:
            self.skipTest("No payment method available to create a payment.")
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 10.0,
        })
        payment.currency_amount = 12.75
        self.assertAlmostEqual(
            payment.currency_amount,
            12.75,
            places=2,
            msg="currency_amount should be updatable after creation."
        )
  
