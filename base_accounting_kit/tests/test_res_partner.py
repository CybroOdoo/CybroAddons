# -*- coding: utf-8 -*-
from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResPartnerFollowup(TransactionCase):
    """Follow-up fields of the partner"""

    def test_followup_without_invoice_due_date(self):
        """A partner whose unpaid invoices have no due date can be read"""
        partner = self.env['res.partner'].create({'name': 'Followup Partner'})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Service',
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        # The due date of a draft invoice can be cleared
        invoice.invoice_date_due = False
        self.assertFalse(invoice.invoice_date_due)
        self.assertEqual(partner.invoice_list, invoice)
        # Must not raise "min() iterable argument is empty"
        self.assertEqual(partner.get_min_date(), fields.Date.today())
        partner.invalidate_recordset()
        self.assertEqual(partner.total_due, 100.0)
