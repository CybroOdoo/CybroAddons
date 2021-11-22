# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta, date

import dateutil.relativedelta
from dateutil.relativedelta import relativedelta

from odoo import models


class CustomReport(models.AbstractModel):
    _name = "report.top_selling_product_report.top_selling_reports"
    _description = "Top selling products report"

    def _get_report_values(self, docids, data=None):
        limit_value = data['period'] if data['period'] else None
        date_option = data['date']
        date_selected_from = None
        date_selected = None
        date_selected_to = None
        other_details = {}

        company_id = data['company']
        warehouse_id = data['warehouse']

        from_date = date.today() - dateutil.relativedelta.relativedelta(years=100)
        to_date = date.today() + dateutil.relativedelta.relativedelta(days=1)

        if date_option == 'days':

            from_date = date.today() - dateutil.relativedelta.relativedelta(days=11)
            to_date = date.today() + dateutil.relativedelta.relativedelta(days=1)
            date_selected = "Last 10 Days"

        elif date_option == 'last_month':

            date_limit = date.today() - dateutil.relativedelta.relativedelta(months=1)
            from_date = date_limit.replace(day=1)
            to_date = (date_limit + relativedelta(months=1, day=1)) - timedelta(1)
            date_selected = "Last Month"

        elif date_option == 'curr_month':

            from_date = date.today().replace(day=1)
            to_date = date.today() + dateutil.relativedelta.relativedelta(days=1)
            date_selected = "Current Month"

        elif date_option == 'last_year':

            date_limit = date.today() - dateutil.relativedelta.relativedelta(years=1)
            from_date = date_limit.replace(day=1)
            to_date = (date_limit + relativedelta(months=12, day=1)) - timedelta(1)
            date_selected = "Last Year"

        elif date_option == 'curr_year':

            date_limit = date.today() - dateutil.relativedelta.relativedelta(years=1)
            from_date = date.today().replace(month=1, day=1)
            to_date = date.today() + dateutil.relativedelta.relativedelta(days=1)
            date_selected = "Current Year"

        elif date_option == 'select_period':

            from_date = data['from_date']
            to_date = data['to_date']
            date_selected_from = from_date
            date_selected_to = to_date

        other_details.update({

            'limit': limit_value,
            'least': data['least'],
            'range': date_selected,
            'date_selected_from': date_selected_from,
            'date_selected_to': date_selected_to,
        })

        cr = self._cr
        order = 'asc' if data['least'] else 'desc'
        company_id = str(tuple(company_id)) if len(company_id) > 1 else "(" + str(company_id[0]) + ")"
        warehouse_id = str(tuple(warehouse_id)) if len(warehouse_id) > 1 else "(" + str(warehouse_id[0]) + ")"
        limit_clause = " limit'%s'" % limit_value if limit_value else ""

        query = ("""select sl.name as product_name,sum(product_uom_qty),pu.name from sale_order_line sl 
                   JOIN sale_order so ON sl.order_id = so.id 
                   JOIN uom_uom pu on sl.product_uom = pu.id
                   where so.date_order::DATE >= '%s'::DATE and 
                   so.date_order::DATE <= '%s'::DATE and 
                   sl.state = 'sale' and so.company_id in %s 
                   and so.warehouse_id in %s
                   group by sl.name,pu.name order by sum %s""" % (
            from_date, to_date, company_id, warehouse_id, order)) + limit_clause
        cr.execute(query)
        dat = cr.dictfetchall()

        return {
            'data': dat,
            'other': other_details,
        }
