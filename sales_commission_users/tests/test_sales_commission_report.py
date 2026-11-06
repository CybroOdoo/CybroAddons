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
from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSalesCommissionReport(TransactionCase):
    """Tests for report wizard validation and report data selection."""

    def test_report_wizard_rejects_start_date_after_end_date(self):
        with self.assertRaises(ValidationError):
            self.env['sales.commission.report'].create({
                'start_date': '2026-02-02',
                'end_date': '2026-02-01',
            })

    def test_report_values_filter_by_salesperson_and_inclusive_date_range(self):
        other_salesperson = self.env['res.users'].create({
            'name': 'Report salesperson',
            'login': 'report-commission-salesperson-test',
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        })
        CommissionLine = self.env['commission.lines']
        in_range = CommissionLine.create({
            'date': '2026-02-01',
            'sales_person_id': self.env.user.id,
            'description': 'Included commission',
        })
        before_range = CommissionLine.create({
            'date': '2026-01-31',
            'sales_person_id': self.env.user.id,
            'description': 'Earlier commission',
        })
        other_salesperson_line = CommissionLine.create({
            'date': '2026-02-01',
            'sales_person_id': other_salesperson.id,
            'description': 'Other salesperson commission',
        })

        values = self.env[
            'report.sales_commission_users.report_sales_commission'
        ]._get_report_values([], data={
            'sales_person_id': self.env.user.id,
            'start_date': '2026-02-01',
            'end_date': '2026-02-28',
        })

        self.assertEqual(values['doc_model'], 'commission.lines')
        self.assertEqual(values['docs'], in_range)
        self.assertNotIn(before_range, values['docs'])
        self.assertNotIn(other_salesperson_line, values['docs'])

    def test_report_values_can_use_explicit_document_ids(self):
        lines = self.env['commission.lines'].create([
            {'description': 'First report line'},
            {'description': 'Second report line'},
        ])
        values = self.env[
            'report.sales_commission_users.report_sales_commission'
        ]._get_report_values(lines.ids, data={})
        self.assertEqual(values['docs'], lines)
        self.assertEqual(values['doc_ids'], lines.ids)

