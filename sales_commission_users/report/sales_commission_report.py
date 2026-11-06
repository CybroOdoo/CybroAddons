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


class SalesCommissionReportAbstract(models.AbstractModel):
    """Abstract model to prepare values for sales commission report."""
    _name = 'report.sales_commission_users.report_sales_commission'
    _description = 'Sales Commission Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare values for the sales commission report."""
        data = data or {}
        if docids:
            docs = self.env['commission.lines'].browse(docids)
            return {
                'doc_ids': docids,
                'doc_model': 'commission.lines',
                'docs': docs,
                'data': data,
            }
        domain = []
        if data.get('sales_person_id'):
            domain.append(('sales_person_id', '=', data['sales_person_id']))
        if data.get('start_date'):
            domain.append(('date', '>=', data['start_date']))
        if data.get('end_date'):
            domain.append(('date', '<=', data['end_date']))
        docs = self.env['commission.lines'].search(domain)
        return {
            'doc_ids': docids,
            'doc_model': 'commission.lines',
            'docs': docs,
            'data': data,
        }
