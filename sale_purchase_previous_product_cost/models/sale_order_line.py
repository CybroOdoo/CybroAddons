#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Inherited SaleOrderLine to add custom fields and methods actions"""
    _inherit = 'sale.order.line'

    sale_date = fields.Datetime(string='Sale Date', help='Sale Order date',
                                related='order_id.date_order', store=True)

    def action_get_product_form(self):
        """This function opens the product form from the sale order line"""
        self.ensure_one()
        if self.product_id:
            return {
                'name': self.product_id.name,
                'view_mode': 'form',
                'res_model': 'product.product',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.product_id.id,
                'context': dict(
                    self.env.context,
                    default_order_partner_id=self.order_id.partner_id.id,
                ),
            }
        return {'type': 'ir.actions.act_window_close'}