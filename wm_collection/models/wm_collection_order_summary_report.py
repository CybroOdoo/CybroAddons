# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models


class ReportCollectionOrderSummary(models.AbstractModel):
    """QWeb report parser model generating aggregated collection order summary sheets."""
    _name = 'report.wm_collection.report_collection_order_summary_document'
    _description = 'Collection Order Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Aggregate collection order data by partner, category, and date range to
        populate the collection order summary report table with totals and
        sub-totals.
        """
        docs = self.env['wm.collection.order.report.wizard'].browse(docids)
        report_data = {}

        for doc in docs:
            domain = [
                ('scheduled_start', '>=', doc.date_from),
                ('scheduled_start', '<=', doc.date_to)
            ]
            if doc.order_id:
                domain.append(('id', '=', doc.order_id.id))
            if doc.state:
                domain.append(('state', '=', doc.state))
            if doc.route_id:
                domain.append(('route_id', '=', doc.route_id.id))
            if doc.product_id:
                domain.append(('order_line_ids.product_id', '=', doc.product_id.id))

            orders = self.env['wm.collection.order'].search(domain, order='scheduled_start desc')

            report_data[doc.id] = {
                'total_orders': len(orders),
                'total_completed': len(orders.filtered(lambda o: o.state in ['completed', 'signed', 'invoiced'])),
                'total_missed': len(orders.filtered(lambda o: o.state == 'missed')),
                'records': orders,
            }

        return {
            'docs': docs,
            'report_data': report_data,
        }
