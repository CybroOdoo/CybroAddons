# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.fields import Datetime


@tagged('post_install', '-at_install')
class TestInvoicePayment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({
            'name': 'Invoice Client',
            'email': 'invoice@example.com',
            'phone': '1234567890'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Invoice Category'
        })
        cls.lawyer = cls.env['hr.employee'].create({
            'name': 'Invoice Lawyer',
            'is_lawyer': True,
            'wage_per_case': 2000,
            'wage_per_trial': 200,
        })
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'description': 'Invoice Case',
            'lawyer_id': cls.lawyer.id,
        })
        cls.case.action_confirm()

    def test_onchange_case_id(self):
        """Test the logic that toggles trial selection and cost"""
        wizard = self.env['invoice.payment'].new({'case_id': self.case.id})

        # Test payment_method = trial
        self.case.payment_method = 'trial'
        trial = self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        })
        wizard._onchange_case_id()
        self.assertFalse(wizard.is_trial_hide)
        self.assertEqual(wizard.cost, self.lawyer.wage_per_trial)
        self.assertIn(trial.id, wizard.trial_ids.ids)

        # Test payment_method = case
        self.case.payment_method = 'case'
        wizard._onchange_case_id()
        self.assertTrue(wizard.is_cost_hide)

        # Test payment_method = out_of_court
        self.case.payment_method = 'out_of_court'
        wizard._onchange_case_id()
        self.assertFalse(wizard.is_cost_hide)

    def test_action_print_invoice_case(self):
        """Test action_print_invoice for per-case payment method"""
        self.case.payment_method = 'case'
        wizard = self.env['invoice.payment'].create({
            'case_id': self.case.id,
            'cost': 2000,
        })
        action = wizard.action_print_invoice()
        self.assertEqual(self.case.state, 'invoiced')
        self.assertEqual(action['res_model'], 'account.move')

        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.case_ref, self.case.name)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 2000)

    def test_action_print_invoice_trial(self):
        """Test action_print_invoice for per-trial payment method"""
        self.case.payment_method = 'trial'
        trial1 = self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        })
        trial2 = self.env['legal.trial'].create({
            'case_id': self.case.id,
            'trial_date': Datetime.now(),
        })
        wizard = self.env['invoice.payment'].create({
            'case_id': self.case.id,
            'cost': 200,
            'trial_ids': [(6, 0, [trial1.id, trial2.id])],
            'is_last_trial': True,
        })
        action = wizard.action_print_invoice()
        self.assertEqual(self.case.state, 'invoiced')
        self.assertTrue(trial1.is_invoiced)
        self.assertTrue(trial2.is_invoiced)
        self.assertEqual(action['res_model'], 'account.move')

        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.case_ref, self.case.name)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 400) # 200 * 2 trials

    def test_action_print_invoice_out_of_court(self):
        """Test action_print_invoice for out of court payment method"""
        self.case.payment_method = 'out_of_court'
        wizard = self.env['invoice.payment'].create({
            'case_id': self.case.id,
            'cost': 1500,
        })
        action = wizard.action_print_invoice()
        self.assertEqual(self.case.state, 'invoiced')
        self.assertEqual(action['res_model'], 'account.move')

        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.case_ref, self.case.name)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 1500)
        self.assertEqual(invoice.invoice_line_ids[0].name, 'Out of Court Settlement')
