# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
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

###############################################################################
from odoo import api, models


class InventoryPDFReport(models.AbstractModel):
    """This abstract model is used for generating an inventory PDF report.
    This model serves as a template for generating PDF reports related
    to inventory data. It is designed to be used as a base for specific
    report generators."""
    _name = 'report.inventory_report_generator.inventory_pdf_report'
    _description = 'Inventory PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for generating an inventory PDF report.
        docids: IDs of the documents to be included in the report.
        data: Additional data or options for generating the report.
        return: A dictionary containing the report data and parameters."""
        if self.env.context.get('inventory_pdf_report'):
            report_data = data.get('report_data') or {}
            filters = dict(report_data.get('filters') or {})
            orders = report_data.get('orders') or {}
            if orders.get('date_from'):
                filters['date_from'] = orders['date_from']
            if orders.get('date_to'):
                filters['date_to'] = orders['date_to']
            data.update({
                'report_main_line_data': report_data.get('report_lines', []),
                'Filters': filters,
                'Dates': orders,
                'company': self.env.company,
            })
        return data
