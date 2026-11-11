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
from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.model.id, 'license_plate': 'TEST-INV-001'})

        # create a car.rental.contract for the fleet_rent_id
        cls.contract = cls.env['car.rental.contract'].create({
            'customer_id': cls.customer.id,
            'vehicle_id': cls.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today(),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'state': 'running',
        })

        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'journal_id': cls.journal.id,
            'fleet_rent_id': cls.contract.id,
        })

    def test_button_cancel(self):
        """ Test button cancel for invoice linked to rental contract """
        # When contract state is 'running'
        self.invoice.button_cancel()
        self.assertEqual(self.contract.state, 'running')
        self.assertFalse(self.contract.first_invoice_created)

        # When contract state is not 'running'
        self.contract.state = 'done'
        self.invoice.button_draft()
        self.invoice.button_cancel()
        self.assertEqual(self.contract.state, 'checking')

    def test_account_move_line_onchange_price_unit(self):
        """ Test onchange price unit updates contract first payment """
        line = self.env['account.move.line'].new({
            'move_id': self.invoice,
            'price_unit': 250.0,
        })
        line._onchange_price_unit()
        self.assertEqual(self.contract.first_payment, 250.0)

    @patch('odoo.addons.account.wizard.account_payment_register.AccountPaymentRegister.action_create_payments',
           return_value=True)
    def test_payment_register_first_invoice(self, mock_action):
        """ Test account.payment.register sending email on first rental invoice payment """
        self.customer.email = 'customer@test.com'
        self.invoice.name = 'INV/2026/00001'
        self.invoice.is_first_invoice = True
        self.contract.first_payment_inv = self.invoice.id
        self.contract.first_invoice_created = True

        wizard = self.env['account.payment.register'].new({
            'communication': self.invoice.name,
        })
        wizard.action_create_payments()
        self.assertTrue(mock_action.called)
        mail = self.env['mail.mail'].search([('email_to', '=', self.customer.email)], order='id desc', limit=1)
        self.assertTrue(mail)
        self.assertIn('INV/2026/00001', mail.subject)
        self.assertEqual(self.contract.first_payment_inv, self.invoice)
        self.assertTrue(self.contract.first_invoice_created)
        self.assertTrue(self.invoice.is_first_invoice)

    @patch('odoo.addons.account.wizard.account_payment_register.AccountPaymentRegister.action_create_payments')
    def test_payment_register_recurrent_invoice(self, mock_action):
        """ Test account.payment.register sending email on recurrent rental invoice payment """
        self.customer.email = 'customer@test.com'
        rec_inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'name': 'INV/2026/00002',
            'fleet_rent_id': self.contract.id,
            'is_first_invoice': False,
        })
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=rec_inv.ids,
        ).new({
            'communication': rec_inv.name,
        })
        wizard.action_create_payments()
        self.assertTrue(mock_action.called)
        mail = self.env['mail.mail'].search([('email_to', '=', self.customer.email)], order='id desc', limit=1)
        self.assertTrue(mail)
        self.assertIn('INV/2026/00002', mail.subject)
        self.assertIn('Recurrent Payment Received', rec_inv.message_ids[0].body)
