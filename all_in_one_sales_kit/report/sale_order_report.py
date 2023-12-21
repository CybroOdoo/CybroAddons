# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, models


class SaleOrderReport(models.AbstractModel):
    """It is to add new abstract model for sale_order_report."""
    _name = 'report.all_in_one_sales_kit.sale_order_report'
    _description = "Sale Order Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """It is to pass report values."""
        if self.env.context.get('sale_order_report'):
            if data.get('report_data'):
                report_lines = data.get('report_data')['report_lines']
                total_amount = sum(
                    line.get('amount_total', 0) for line in report_lines)
                data.update({'report_main_line_data': report_lines,
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             'total_amount': total_amount,
                             })
            return data
