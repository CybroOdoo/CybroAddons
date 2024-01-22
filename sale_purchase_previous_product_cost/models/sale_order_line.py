# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Inherited to add field sale date in sales order line"""
    _inherit = 'sale.order.line'

    sale_date = fields.Datetime(string='Sale Date', help='Sale Order date',
                                related='order_id.date_order', store=True)

    def action_get_product_form(self):
        """This function is to view product form in sale order line"""
        self.product_id.order_partner_id = self.order_id.partner_id.id
        return {
            'name': self.product_id.name,
            'view_mode': 'form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.product_id.id
        }
