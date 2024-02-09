# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models, _


class InventoryPDFReport(models.AbstractModel):
    """This abstract model is used for generating an inventory PDF report.
    This model serves as a template for generating PDF reports related
    to inventory data. It is designed to be used as a base for specific
    report generators."""
    _name = 'report.inventory_report_generator.inventory_pdf_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for generating an inventory PDF report.
        docids: IDs of the documents to be included in the report.
        data: Additional data or options for generating the report.
        return: A dictionary containing the report data and parameters."""
        if self.env.context.get('inventory_pdf_report'):
            data.update({'report_main_line_data': data.get('report_data')[
                'report_lines'],
                         'Filters': data.get('report_data')['filters'],
                         'Dates': data.get('report_data')['orders'],
                         'company': self.env.company,
                         })
        return data
