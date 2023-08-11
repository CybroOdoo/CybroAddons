# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherits the sale order for checking the quantities and rise the error
         when the product is not available"""
    _inherit = 'sale.order'

    onhand_check = fields.Boolean(string='Enable OnHand',
                                  help='To check whether it is based on '
                                       'on hand quantity')
    forecast_check = fields.Boolean(string='Enable Forecast',
                                    help='To check whether it is based on'
                                         'Forecast quantity')

    def action_confirm(self):
        """Inherits the function and compare the quantities of products. Raise
        error when the quantity is less than available."""
        res = super(SaleOrder, self).action_confirm()
        low_qty = []
        product_restriction = self.env['ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.product_restriction')
        check_stock = self.env['ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.check_stock')
        if product_restriction:
            for rec in self.order_line:
                if rec.product_id.detailed_type == 'product':
                    if check_stock == 'on_hand_quantity' and \
                            rec.product_uom_qty > rec.available_qty:
                        low_qty.append(
                            "You have added %s units of %s but you only"
                            " have %s units available.\n" % (
                                rec.product_uom_qty, rec.product_id.name,
                                rec.available_qty))
                    elif check_stock == 'forecast_quantity' and \
                            rec.product_uom_qty > rec.available_qty:
                        low_qty.append(
                            "You have added %s units of %s but you only "
                            "have %s units available.\n" % (
                                rec.product_uom_qty, rec.product_id.name,
                                rec.available_qty))
        if low_qty:
            raise UserError(
                "Can't confirm the sale order due to: \n" + ' '.join(
                    map(str, low_qty)))
        return res
