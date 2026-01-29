# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, models


class PosAnalysisReport(models.AbstractModel):
    """
    This model provides functionality to dynamically generate a
    Point of Sale (POS) analysis report in PDF format
    """
    _name = 'report.pos_analysis_report.report_pos_analysis'
    _description = 'Get pos analysis result as PDF'

    @api.model
    def _get_report_values(self, docids, data):
        """
         override the method to create custom report with custom values
         :param docids: the recordset/ record from which the report
         action is invoked
         :param data: report data
         :return: data and recodsets to be used in the report template
        """
        query = """SELECT 
                    pos_session.name AS session, 
                    pos_order.name AS Order_Ref,
                    pos_order.pos_reference AS receipt_ref,
                    pos_order.date_order AS order_date,
                    CASE WHEN res_partner.id IS NULL THEN NULL ELSE 
                    res_partner.name END AS customer,
                    pos_order.amount_paid AS sub_total,
                    pos_order.amount_tax AS tax
                FROM 
                    pos_session 
                INNER JOIN 
                    pos_order ON pos_session.id = pos_order.session_id
                LEFT JOIN 
                    res_partner ON pos_order.partner_id = res_partner.id"""
        where_clause = []
        params = []
        if data['from_date'] and data['to_date']:
            where_clause.append("pos_order.date_order BETWEEN %s AND %s")
            params.extend([data['from_date'], data['to_date']])
        if data['pos_session_id']:
            where_clause.append("pos_session.id = %s")
            params.append(data['pos_session_id'])
        if data['partner_id']:
            where_clause.append("res_partner.id = %s")
            params.append(data['partner_id'])
        if where_clause:
            where_clause_str = " WHERE " + " AND ".join(where_clause)
            query += where_clause_str
        self.env.cr.execute(query, tuple(params))
        pos_orders = self.env.cr.dictfetchall()
        grant_total = sum(pos_order.get('sub_total', 0)
                          for pos_order in pos_orders)
        return {
            'doc_ids': docids,
            'data': data,
            'result': pos_orders,
            'grant_tot': grant_total
        }
