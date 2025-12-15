# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P(odoo@cybrosys.com)
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
#############################################################################
from odoo import api, models


class SalesCommissionReportAbstract(models.AbstractModel):
    """To create report for sales commission"""
    _name = 'report.sales_commission_users.report_sales_commission'
    _description = 'Sales Commission Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """To get values of for the report for sales commission for a sales
         person"""
        sale_commission_id = self.env['commission.lines'].browse(docids)
        if docids:
            return {
                'doc_ids ': docids,
                'doc_model': 'commission.lines',
                'docs': sale_commission_id,
                'data': data
            }
        else:
            domain = []
            if data.get('sales_person_id'):
                domain.append(
                    ('sales_person_id', '=', data['sales_person_id']))
            if data.get('start_date'):
                domain.append(('date', '>=', data['start_date']))
            if data.get('end_date'):
                domain.append(('date', '<=', data['end_date']))
            docs = self.env['commission.lines'].search(domain)
            return {
                'doc_ids ': docids,
                'doc_model': 'commission.lines',
                'docs': docs,
                'data': data
            }
