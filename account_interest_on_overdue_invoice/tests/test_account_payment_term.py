# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestAccountPaymentTerms(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountPaymentTerms, cls).setUpClass()
        cls.account_payment_term = cls.env['account.payment.term']

    def test_check_interest_percentage_positive(self):
        """Test that positive interest percentage does not raise ValidationError."""
        payment_term = self.account_payment_term.create({
            'name': 'Positive Interest Term',
            'interest_overdue_act': True,
            'interest_percentage': 5.0,
        })
        self.assertTrue(payment_term)

    def test_check_interest_percentage_zero(self):
        """Test that zero interest percentage raises ValidationError when interest is active."""
        with self.assertRaises(ValidationError):
            self.account_payment_term.create({
                'name': 'Zero Interest Term',
                'interest_overdue_act': True,
                'interest_percentage': 0.0,
            })

    def test_check_interest_percentage_negative(self):
        """Test that negative interest percentage raises ValidationError when interest is active."""
        with self.assertRaises(ValidationError):
            self.account_payment_term.create({
                'name': 'Negative Interest Term',
                'interest_overdue_act': True,
                'interest_percentage': -2.0,
            })

    def test_check_interest_percentage_inactive(self):
        """Test that zero or negative interest percentage does not raise ValidationError when interest is inactive."""
        payment_term = self.account_payment_term.create({
            'name': 'Inactive Interest Term',
            'interest_overdue_act': False,
            'interest_percentage': 0.0,
        })
        self.assertTrue(payment_term)
