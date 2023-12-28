# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import dateutil.relativedelta
from dateutil.relativedelta import relativedelta
from datetime import timedelta, date
from odoo import models


class TopSellingReport(models.AbstractModel):
    """The CustomReport abstract Model is used to generate a top-selling
    products report based on various date options."""
    _name = "report.top_selling_product_report.top_selling_reports"
    _description = "Top selling products report"

    def _get_report_values(self, docids, data=None):
        """Generate the data for the top-selling products report.
        Args:
            data (dict): A dictionary containing the parameters for the report.
        Returns:
            dict: A dictionary containing the data and other details of the
            top-selling products report."""
        limit_value = int(data['period']) if data['period'] else None
        date_option = data['date']
        date_selected_from = None
        date_selected = None
        date_selected_to = None
        other_details = {}
        company_id = data['company']
        warehouse_id = data['warehouse']
        from_date = date.today() - dateutil.relativedelta.relativedelta(
            years=100)
        to_date = date.today() + dateutil.relativedelta.relativedelta(days=1)
        if date_option == 'days':
            from_date = date.today() - dateutil.relativedelta.relativedelta(
                days=11)
            to_date = date.today() + dateutil.relativedelta.relativedelta(
                days=1)
            date_selected = "Last 10 Days"
        elif date_option == 'last_month':
            date_limit = date.today() - dateutil.relativedelta.relativedelta(
                months=1)
            from_date = date_limit.replace(day=1)
            to_date = (date_limit + relativedelta(months=1,
                                                  day=1)) - timedelta(1)
            date_selected = "Last Month"
        elif date_option == 'curr_month':
            from_date = date.today().replace(day=1)
            to_date = date.today() + dateutil.relativedelta.relativedelta(
                days=1)
            date_selected = "Current Month"
        elif date_option == 'last_year':
            date_limit = date.today() - dateutil.relativedelta.relativedelta(
                years=1)
            from_date = date_limit.replace(day=1)
            to_date = (date_limit + relativedelta(months=12,
                                                  day=1)) - timedelta(1)
            date_selected = "Last Year"
        elif date_option == 'curr_year':
            from_date = date.today().replace(month=1, day=1)
            to_date = date.today() + dateutil.relativedelta.relativedelta(
                days=1)
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
        sale_report_model = self.env['sale.report']
        states = sale_report_model._get_done_states()
        data_domain = [('state', 'in', states), ('date', '>=', from_date),
                       ('date', '<=', to_date),
                       ('company_id', 'in', company_id)]
        if warehouse_id:
            data_domain.append(('warehouse_id', 'in', warehouse_id))
        sale_data = sale_report_model.search(data_domain)
        product_dict = {}
        for record in sale_data:
            product_name = record.product_id.display_name
            if product_name in product_dict:
                product_dict[product_name][
                    'sold_quantity'] += record.product_uom_qty
            else:
                product_dict[product_name] = {
                    'product_name': product_name,
                    'sold_quantity': record.product_uom_qty,
                    'uom': record.product_uom.name,
                }
        sorted_products = sorted(product_dict.values(),
                                 key=lambda x: x['sold_quantity'],
                                 reverse=not data['least'])
        limit_products = sorted_products[:limit_value]
        return {
            'data': limit_products,
            'other': other_details,
        }
