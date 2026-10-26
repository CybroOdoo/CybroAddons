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
from odoo import api, models


class LoanDetails(models.AbstractModel):
    """Fetch PDF report values"""
    _name = 'report.advanced_loan_management.loan_report_template'
    _description = 'Loan Report'

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        loan_id = self.env['loan.request'].browse(doc_ids[:1]) if doc_ids else self.env['loan.request']
        partner = loan_id.partner_id
        data = {
            'Loan_id': loan_id.id,
            'Customer': partner.name or '',
            'CustomerAddress': f"{partner.street or ''} {partner.city or ''}".strip(),
            'CustomerAddress2': f"{partner.city or ''}, {partner.state_id.name or ''}".strip(', '),
            'CustomerContact': partner.phone or '',
            'Loan_Type': loan_id.loan_type_id.name or '',
            'Tenure': loan_id.tenure or 0,
            'Tenure_type': loan_id.loan_type_id.tenure_plan or '',
            'Interest_Rate': str((loan_id.interest_rate or 0.0) * 100),
            'Loan_Amount': str(loan_id.loan_amount or 0.0),
        }
        if loan_id:
            query = """
                SELECT name, date, amount, interest_amount, state, total_amount
                FROM repayment_line
                WHERE loan_id = %s
                ORDER BY date ASC
            """
            self.env.cr.execute(query, (loan_id.id,))
            record_sort = self.env.cr.dictfetchall()
        else:
            record_sort = []
        return {
            'docs': record_sort,
            'doc_ids': doc_ids,
            'data': data,
        }
