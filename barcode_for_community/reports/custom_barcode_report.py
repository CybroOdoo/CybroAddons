# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models


class BarcodeDataReport(models.AbstractModel):
    """
    Barcode data report model for generating custom barcode PDF reports.
    """
    _name = "report.barcode_for_community.barcode_data_report"
    _description = "Custom Barcode Pdf Report"

    def _get_report_values(self, docids, data):
        """Return report values for rendering the custom barcode PDF report."""
        model = data.get('mode')
        data = {
            'mode': model,
        }
        if model == 'product.product':
            data['items'] = self.env[model].search_read([], ['name', 'barcode'])
        elif model == 'stock.picking.type':
            data['items'] = self.env[model].search_read([], ['name', 'barcode'])
        elif model == 'stock.location':
            data['items'] = self.env['stock.location'].search_read([("usage", "=", "internal")], ['name', 'barcode'])
        return data
