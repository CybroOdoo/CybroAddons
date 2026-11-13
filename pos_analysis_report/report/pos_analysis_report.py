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
from datetime import datetime, time

import pytz

from odoo import api, fields, models


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
        domain = []
        try:
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc

        if data.get('from_date') and data.get('to_date'):
            from_dt = user_tz.localize(datetime.combine(
                fields.Date.to_date(data['from_date']), time.min
            )).astimezone(pytz.utc).replace(tzinfo=None)
            to_dt = user_tz.localize(datetime.combine(
                fields.Date.to_date(data['to_date']), time.max
            )).astimezone(pytz.utc).replace(tzinfo=None)
            domain.extend([('date_order', '>=', from_dt),
                           ('date_order', '<=', to_dt)])
        elif data.get('from_date'):
            from_dt = user_tz.localize(datetime.combine(
                fields.Date.to_date(data['from_date']), time.min
            )).astimezone(pytz.utc).replace(tzinfo=None)
            domain.append(('date_order', '>=', from_dt))
        elif data.get('to_date'):
            to_dt = user_tz.localize(datetime.combine(
                fields.Date.to_date(data['to_date']), time.max
            )).astimezone(pytz.utc).replace(tzinfo=None)
            domain.append(('date_order', '<=', to_dt))
        if data.get('pos_session_id'):
            domain.append(('session_id', '=', data['pos_session_id']))
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data['partner_id']))

        orders = self.env['pos.order'].search(domain)
        pos_orders = []
        for order in orders:
            pos_orders.append({
                'session': order.session_id.name,
                'order_ref': order.name,
                'receipt_ref': order.pos_reference,
                'order_date': order.date_order,
                'customer': order.partner_id.name if order.partner_id else None,
                'sub_total': round(order.amount_total - order.amount_tax, 2),
                'tax': order.amount_tax,
            })
        grant_total = sum(pos_order.get('sub_total', 0)
                          for pos_order in pos_orders)
        partner_name = False
        if data.get('partner_id'):
            partner = self.env['res.partner'].browse(data['partner_id'])
            partner_name = partner.name
        return {
            'doc_ids': docids,
            'data': data,
            'from_date': data.get('from_date'),
            'to_date': data.get('to_date'),
            'partner_id': data.get('partner_id'),
            'partner_name': partner_name,
            'result': pos_orders,
            'grant_tot': grant_total,
        }
