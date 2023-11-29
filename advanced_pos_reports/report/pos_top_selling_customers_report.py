# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
        if order_ids:
            query = """
                       SELECT partner.id, partner.name,
                            sum(amount_total) as amount FROM pos_order, 
                            res_partner AS partner 
                            WHERE partner.id= pos_order.partner_id AND 
                        pos_order.id IN %s GROUP BY partner.id, partner.name
                             ORDER BY amount DESC
                    """
            if no_of_customers > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query,
                                    (tuple(order_ids.ids), no_of_customers))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))
        customers = self.env.cr.dictfetchall()
        return {
            'customers': customers or [],
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(self.get_top_selling_customers_details(
            data['no_of_customers'], data['start_date'], data['end_date']))
        return data
