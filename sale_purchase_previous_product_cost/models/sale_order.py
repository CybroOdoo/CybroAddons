# -*- encoding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, api, fields
from odoo.exceptions import Warning


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def set_partner(self):
        for each in self:
            print each.order_id.partner_id.id
            if each.product_id:
                each.product_id.write({'order_partner_id': each.order_id.partner_id.id})

    sale_data = fields.Datetime(comodel_name='sale.order', string='Sale Date',
                                related='order_id.date_order', store=True)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def set_partner(self):
        for each in self:
            print each.order_id.partner_id.id
            if each.product_id:
                each.product_id.write({'order_partner_id': each.order_id.partner_id.id})

    purchase_data = fields.Datetime(comodel_name='purchase.order', string='Purchase Date',
                                    related='order_id.date_order', store=True)


class ProductTemplate(models.Model):
    _inherit = "product.product"

    order_partner_id = fields.Many2one('res.partner', string="Partner")

    @api.multi
    def action_sale_product_prices(self):
        rel_view_id = self.env.ref(
            'sale_purchase_previous_product_cost.last_sale_product_prices_view')
        sale_lines = self.env['sale.order.line'].search([('product_id', '=', self.id),
                                  ('order_partner_id', '=', self.order_partner_id.id)],
                                 order='create_date DESC')
        if not sale_lines:
            raise Warning("No sales history found.!")
        else:
            return {
                'view_type': 'tree',
                'view_mode': 'tree',
                'res_model': 'sale.order.line',
                'views': [(rel_view_id.id, 'tree')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': "[('id','in',[" + ','.join(map(str, sale_lines.ids)) + "])]",
            }

    @api.multi
    def action_purchase_product_prices(self):
        rel_view_id = self.env.ref(
            'sale_purchase_previous_product_cost.last_sale_product_purchase_prices_view')
        purchase_lines = self.env['purchase.order.line'].search([('product_id', '=', self.id),
                                                                 ('partner_id', '=', self.order_partner_id.id)],
                                                                order='create_date DESC')
        if not purchase_lines:
            raise Warning("No purchase history found.!")
        else:
            return {
                'view_type': 'tree',
                'view_mode': 'tree',
                'res_model': 'purchase.order.line',
                'views': [(rel_view_id.id, 'tree')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': "[('id','in',[" + ','.join(map(str, purchase_lines.ids)) + "])]",
            }



