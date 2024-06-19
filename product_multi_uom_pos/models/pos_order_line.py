# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arwa V V (Contact : odoo@cybrosys.com)
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
            values['uom_id'] = values['product_uom_id']
        return super(PosOrderLine, self).create(values)


class PosOrder(models.Model):
    """
        Model representing Point of Sale orders, inherits from 'pos.order'.
        This class extends functionality related to order lines.
    """
    _inherit = 'pos.order'

    def _get_fields_for_order_line(self):
        """
            Get the fields required for the order line.
            Returns:
                list: A list of fields required for the order line.
        """
        fields = super(PosOrder, self)._get_fields_for_order_line()
        fields.extend(['product_uom_id'])
        return fields

    def _prepare_order_line(self, order_line):
        """
            Prepare the order line data before processing.
            Args:
                order_line (dict): The dictionary representing the order line data.
            Returns:
                dict: The modified order line dictionary with necessary adjustments.
        """
        order_line = super()._prepare_order_line(order_line)
        if order_line["product_uom_id"]:
            order_line["product_uom_id"] = order_line["product_uom_id"][0]
        return order_line
