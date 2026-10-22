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
from odoo import api, fields, models


class ReportPosTopSellingCustomers(models.AbstractModel):
    """Generate top_selling customers report of pos"""
    _name = 'report.advanced_pos_reports.report_pos_top_selling_customers'
    _description = "Report for Top Selling POS Customers"

    def get_top_selling_customers_details(self, no_of_customers=None,
                                          start_date=False, end_date=False):
        """Get top_selling customers details"""
        order_ids = self.env["pos.order"].search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', 'in', ['paid', 'done', 'invoiced'])])
        customers = []
        if order_ids:
            query = """
                SELECT partner.id, partner.name,
                       sum(pos_order.amount_total) AS amount
                FROM pos_order
                INNER JOIN res_partner AS partner ON partner.id = pos_order.partner_id
                WHERE pos_order.id IN %s
                GROUP BY partner.id, partner.name
                ORDER BY amount DESC
            """
            if no_of_customers and no_of_customers > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query, (tuple(order_ids.ids), no_of_customers))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))

            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                customers.append(row)

        return {
            'customers': customers,
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(self.get_top_selling_customers_details(
            data.get('no_of_customers'), data.get('start_date'), data.get('end_date')))
        return data
