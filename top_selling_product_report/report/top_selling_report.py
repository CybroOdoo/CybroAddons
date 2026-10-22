# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import _, models


class TopSellingReport(models.AbstractModel):
    """The CustomReport abstract model is used to generate a top-selling
    products report based on various date options."""
    _name = "report.top_selling_product_report.top_selling_reports"
    _description = "Top Selling Products Report"

    def _get_report_values(self, docids, data=None):
        """Generate the data for the top-selling products report.
        Args:
            data (dict): A dictionary containing the parameters for the report.
        Returns:
            dict: A dictionary containing the data and other details of the
            top-selling products report."""
        try:
            limit_value = int(data['period']) if data['period'] else None
        except (ValueError, TypeError):
            limit_value = None
        date_option = data['date']
        date_selected_from = None
        date_selected = None
        date_selected_to = None
        other_details = {}
        company_id = data['company']
        warehouse_id = data['warehouse']
        today = date.today()
        from_date = datetime.combine(
            today - relativedelta(years=100), datetime.min.time())
        to_date = datetime.combine(
            today + relativedelta(days=1), datetime.min.time())
        if date_option == 'days':
            from_date = datetime.combine(
                today - relativedelta(days=11), datetime.min.time())
            to_date = datetime.combine(
                today + relativedelta(days=1), datetime.min.time())
            date_selected = _("Last 10 Days")
        elif date_option == 'last_month':
            date_limit = today - relativedelta(months=1)
            from_date = datetime.combine(
                date_limit.replace(day=1), datetime.min.time())
            to_date = datetime.combine(
                (date_limit.replace(day=1) + relativedelta(months=1)),
                datetime.min.time())
            date_selected = _("Last Month")
        elif date_option == 'curr_month':
            from_date = datetime.combine(
                today.replace(day=1), datetime.min.time())
            to_date = datetime.combine(
                today + relativedelta(days=1), datetime.min.time())
            date_selected = _("Current Month")
        elif date_option == 'last_year':
            last_year = today.year - 1
            from_date = datetime.combine(
                date(last_year, 1, 1), datetime.min.time())
            to_date = datetime.combine(
                date(last_year + 1, 1, 1), datetime.min.time())
            date_selected = _("Last Year")
        elif date_option == 'curr_year':
            from_date = datetime.combine(
                today.replace(month=1, day=1), datetime.min.time())
            to_date = datetime.combine(
                today + relativedelta(days=1), datetime.min.time())
            date_selected = _("Current Year")
        elif date_option == 'select_period':
            from_date = datetime.combine(data['from_date'], datetime.min.time()) \
                if isinstance(data['from_date'], date) else data['from_date']
            to_date = datetime.combine(
                data['to_date'] + timedelta(days=1), datetime.min.time()) \
                if isinstance(data['to_date'], date) else data['to_date']
            date_selected_from = data['from_date']
            date_selected_to = data['to_date']
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
                       ('date', '<', to_date),
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
                    'uom': record.product_uom_id.name,
                }
        sorted_products = sorted(product_dict.values(),
                                 key=lambda x: x['sold_quantity'],
                                 reverse=not data['least'])
        limit_products = sorted_products[:limit_value]
        return {
            'data': limit_products,
            'other': other_details,
        }
