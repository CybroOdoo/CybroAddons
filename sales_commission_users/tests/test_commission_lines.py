# -*- coding: utf-8 -*-
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
from odoo.exceptions import UserError
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCommissionLines(TransactionCase):
    """Tests for commission line state and invoice action guards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_salesperson = cls.env['res.users'].create({
            'name': 'Other commission salesperson',
            'login': 'other-commission-salesperson-test',
            'group_ids': [Command.set(cls.env.ref('base.group_user').ids)],
        })

    def _create_line(self, **values):
        return self.env['commission.lines'].create({
            'description': 'Commission line',
            'sales_person_id': self.env.user.id,
            'commission_amount': 25,
            'state': 'draft',
            **values,
        })

    def test_empty_recordset_invoice_action_returns_empty_result(self):
        action = self.env['commission.lines'].browse().action_create_invoice()
        self.assertEqual(action, {})

    def test_already_invoiced_line_cannot_be_invoiced_again(self):
        line = self._create_line(state='invoiced')
        with self.assertRaises(UserError):
            line.action_create_invoice()

    def test_invoiced_line_blocks_batch_invoice_action(self):
        draft_line = self._create_line()
        invoiced_line = self._create_line(state='invoiced')
        with self.assertRaises(UserError):
            (draft_line | invoiced_line).action_create_invoice()

    def test_lines_for_different_salespeople_cannot_share_invoice(self):
        first = self._create_line()
        second = self._create_line(sales_person_id=self.other_salesperson.id)
        with self.assertRaises(UserError):
            (first | second).action_create_invoice()

    def test_line_without_salesperson_cannot_be_invoiced(self):
        line = self._create_line(sales_person_id=False)
        with self.assertRaises(UserError):
            line.action_create_invoice()

