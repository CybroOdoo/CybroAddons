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
from odoo import models


class ReportLegalCaseManagementReportLegalCaseDetails(models.AbstractModel):
    """Report of module"""
    _name = 'report.legal_case_management.report_legal_case_details'
    _description = "Report For Case Registration"

    def _get_report_values(self, docids, data=None):
        """This is used to Get data to the pdf"""
        if data is None:
            data = {}

        self.env.flush_all()

        query = """
            SELECT case_reg.name as case_name,
                   case_reg.start_date as start_date,
                   case_reg.end_date as end_date,
                   res_client.name as client,
                   lawyer.name as lawyer,
                   court.name as court,
                   res_judge.name as judge,
                   INITCAP(case_reg.payment_method) as payment_method,
                   INITCAP(case_reg.state) as state
              FROM case_registration case_reg
         LEFT JOIN res_partner res_client ON case_reg.client_id = res_client.id
         LEFT JOIN res_partner res_judge ON case_reg.judge_id = res_judge.id
         LEFT JOIN hr_employee lawyer ON lawyer.id = case_reg.lawyer_id
         LEFT JOIN legal_court court ON case_reg.court_id = court.id
        """
        where_clauses = []
        params = []

        if data.get('lawyer_id'):
            where_clauses.append("lawyer.name = %s")
            params.append(data['lawyer_id'])
        if data.get('client_id'):
            where_clauses.append("res_client.name = %s")
            params.append(data['client_id'])
        if data.get('court_id'):
            where_clauses.append("court.name = %s")
            params.append(data['court_id'])
        if data.get('judge_id'):
            where_clauses.append("res_judge.name = %s")
            params.append(data['judge_id'])
        if data.get('start_date'):
            where_clauses.append("case_reg.start_date = %s")
            params.append(data['start_date'])
        if data.get('end_date'):
            where_clauses.append("case_reg.end_date = %s")
            params.append(data['end_date'])
        if data.get('payment_method'):
            where_clauses.append("case_reg.payment_method = %s")
            params.append(data['payment_method'])
        if data.get('state'):
            where_clauses.append("case_reg.state = %s")
            params.append(data['state'])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY case_reg.id DESC"

        self.env.cr.execute(query, tuple(params))
        docs = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'legal.case.report',
            'data': data,
            'docs': docs,
            'client_id': True,
            'lawyer_id': True,
            'court_id': True,
            'judge_id': True,
            'start_date': True,
            'end_date': True,
            'payment_method': True,
            'state': True,
        }
