# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _


class StockPicking(models.Model):
    """Inherit stock_picking to add barcode field"""
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode', help="Barcode for Scanning Product")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        match = False
        product_id = self.env['product.product'].search(
            [('barcode', '=', self.barcode)], limit=1
        )
        if self.barcode and not product_id:
            self.barcode = False
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _('No product is available for this barcode')
                }
            }
        if self.barcode and self.move_ids_without_package:
            for line in self.move_ids_without_package:
                if line.product_id.barcode == self.barcode:
                    line.quantity += 1
                    match = True
                    break
        if self.barcode and not match and product_id:
            self.barcode = False
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _(
                        'This product is not available in the order. '
                        'You can add it by clicking "Add an item" and scanning again.'
                    )
                }
            }

        self.barcode = False
