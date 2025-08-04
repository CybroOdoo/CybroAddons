# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.info)
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
##############################################################################
from odoo import api, models
from odoo.fields import Date, Datetime


class PurchaseOrderReport(models.AbstractModel):
    """Model for creating pdf report and data fetching """
    _name = 'report.purchase_report_generator.purchase_order_report'
    _description = "Purchase Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function for get pdf report values"""
        if self.env.context.get('purchase_order_report'):
            report_data = data.get('report_data', {})
            orders = report_data.get('orders', {})
            filters = report_data.get('filters', {})
            report_lines = report_data.get('report_lines', [])
            date_from =  Date.from_string(orders.get('date_from', ''))
            date_to = Date.from_string(orders.get('date_to', ''))
            if report_data:
                data.update({
                    'report_main_line_data': report_lines,
                    'Filters': filters,
                    'date_from': (Datetime.from_string(date_from)).strftime('%d/%m/%y') if date_from else '',
                    'date_to': (Datetime.from_string(date_to)).strftime('%d/%m/%y') if date_to else '',
                    'company': self.env.company,
                })
            return data
