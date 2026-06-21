# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFullSettlement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({
            'name': 'Settlement Client',
            'email': 'settlement@example.com',
            'phone': '1234567890'
        })
        cls.category = cls.env['case.category'].create({
            'name': 'Settlement Category'
        })
        cls.lawyer = cls.env['hr.employee'].create({
            'name': 'Settlement Lawyer',
            'is_lawyer': True,
        })
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'description': 'Settlement Case',
            'lawyer_id': cls.lawyer.id,
        })
        cls.case.action_confirm()

    def test_action_print_invoice(self):
        """Test creating full settlement invoice"""
        wizard = self.env['full.settlement'].create({
            'case_id': self.case.id,
            'cost': '5000',
        })
        
        action = wizard.action_print_invoice()
        
        # Verify case state changed to invoiced
        self.assertEqual(self.case.state, 'invoiced')
        
        # Verify action returns account move window
        self.assertEqual(action['res_model'], 'account.move')
        
        # Verify invoice content
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.case_ref, self.case.name)
        self.assertEqual(invoice.partner_id.id, self.client.id)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids[0].name, 'Complete Settlement')
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 5000)
