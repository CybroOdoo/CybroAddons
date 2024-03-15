# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (Contact : odoo@cybrosys.com)
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
from odoo import api, fields, models


class PosOrderLine(models.Model):
    """Inherits model 'pos.order.line' and updates UoM"""
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM',
                                     related='uom_id',
                                     help='Unit of measure of product')
    uom_id = fields.Many2one('uom.uom', string='Product UoM',
                             help='Unit of measure of product added in POS '
                                  'order line')

    @api.model
    def create(self, values):
        """Updates UoM in POS order lines"""
        if values.get('product_uom_id'):
            values['uom_id'] = int(values['product_uom_id'])
        return super().create(values)

    def _export_for_ui(self, orderline):
        """Extends the base '_export_for_ui' method to include the
        'product_uom_id' field in the exported data.
        :param orderline: The POS order line.
        :return: Dictionary with additional data for UI export."""
        result = super()._export_for_ui(orderline)
        result.update({
            'product_uom_id': orderline.product_uom_id.id,
        })
        return result