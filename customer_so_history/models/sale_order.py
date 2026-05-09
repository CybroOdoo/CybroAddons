# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_details_ids = fields.One2many(
        'order.history.line', 'order_id',
        string="Customer Order History",
        help="Displays previous order history lines for the selected customer.")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Load previous confirmed and done order lines for the selected customer."""
        if self.partner_id:
            new_lines = [fields.Command.clear()]
            lines = self.env['sale.order.line'].search(
                [('order_id.partner_id', '=', self.partner_id.id),
                 ('order_id.state', 'in', ('sale', 'done'))])
            for rec in lines:
                new_lines.append(fields.Command.create({
                    'name': rec.order_id.name,
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.product_uom_qty,
                    'price_unit': rec.price_unit,
                    'tax_id': [
                        fields.Command.set([line.id for line in rec.tax_id])],
                    'price_subtotal': rec.price_subtotal
                }))
            self.order_details_ids = new_lines
        else:
            self.order_details_ids = [fields.Command.clear()]
