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


class ResConfigSettings(models.TransientModel):
    """
    Class ResConfigSettings used to print barcode of the location, products and
    inventory commands
    """
    _inherit = 'res.config.settings'

    def action_print_barcode(self):
        """Action for printing different barcodes of the locations, product and
        inventory commands"""
        if self.env.context.get('model') == 'product.product':
            report_name = "Products"
        elif self.env.context.get('model') == 'stock.picking.type':
            report_name = "Operation Types"
        elif self.env.context.get('model') == 'stock.location':
            report_name = "Locations"
        else:
            report_name = "Inventory Commands"
        report = self.env.ref('barcode_for_community.report_barcode_pdf_download')
        report.name = 'Barcode of ' + report_name
        return (self.env.ref('barcode_for_community.report_barcode_pdf_download').
                report_action(self, data={'mode': self.env.context.get('model')}))
