# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abhishek E T (odoo@cybrosys.com)
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
################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MassPriceUpdate(models.TransientModel):
    _name = 'mass.price.update'
    _description = "Change Price and Cost of Products by Percentage"

    name = fields.Char(string='Name', default='Change in Product Price')
    apply_to = fields.Selection([
        ('all', 'All Products'), ('category', 'Selected Categories'),
        ('selected', 'Selected Products')], default='selected',
        string='Apply To', required=True)
    apply_on = fields.Selection([
        ('price', 'Price'), ('cost', 'Cost')], default='price',
        string='Apply On', required=True)
    change = fields.Float(string='Change')
    apply_type = fields.Selection([
        ('add', 'Add'), ('reduce', 'Reduce')], default='add',
        string='Apply Type', required=True)
    product_ids = fields.Many2many(
        'product.product', string='Products', default=False,
        domain="[('active', '=', True)]")
    category_ids = fields.Many2many(
        'product.category', string='Categories', default=False)
    line_ids = fields.One2many('change.price.line', 'mass_price_update_id',
                               string='Lines', readonly=True)

    @api.onchange('apply_to')
    def _onchange_apply_to(self):
        if self.apply_to == 'all':
            self.write({
                'category_ids': [(5,)],
                'line_ids': [(5,)],
                'product_ids': [(6, 0, self.env['product.product'].search(
                    [('active', '=', True)]).ids)]
            })
        elif self.apply_to == 'category':
            self.write({
                'line_ids': [(5,)],
                'product_ids': [(6, 0, self.env['product.product'].search(
                    [('categ_id', 'in', self.category_ids.ids)]).ids)]
            })
        else:
            self.write({
                'product_ids': [(5,)],
                'category_ids': [(5,)],
                'line_ids': [(5,)]
            })

    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        if self.product_ids:
            self.write({'line_ids': [(5,)]})
            lines = []
            for product in self.product_ids:
                lines.append((0, 0, {'product_id': product._origin.id}))
            self.write({'line_ids': lines})

    @api.onchange('category_ids')
    def _onchange_category_ids(self):
        if self.category_ids:
            self.write({'line_ids': [(5,)], 'product_ids': [(5,)]})
            lines = []
            products = self.env['product.product'].sudo().search(
                [('categ_id', 'in', self.category_ids.ids)])
            for product in products:
                lines.append((0, 0, {'product_id': product.id}))
            self.write({
                'product_ids': products.ids,
                'line_ids': lines
            })

    @api.onchange('apply_on')
    def _onchange_apply_on(self):
        if self.apply_on == 'cost':
            self.name = 'Change in Product Cost'
        else:
            self.name = 'Change in Product Price'

    def action_change_price(self):
        """ This function is used to change the price or cost of products """
        if self.apply_to == 'category' and not self.product_ids:
            raise UserError(_("Please select any category with products."))
        if self.apply_to == 'selected' and not self.product_ids:
            raise UserError(_("Please select any product."))
        if not self.change:
            raise UserError(_("Please enter the change in percentage."))
        if self.apply_type == 'add':
            percentage_num = 1 + self.change
        else:
            percentage_num = 1 - self.change
        if self.apply_on == 'price':
            for product in self.product_ids:
                product.lst_price = product.lst_price * percentage_num
        else:
            for product in self.product_ids:
                product_template = product.product_tmpl_id
                product_template.standard_price = (
                        product_template.standard_price * percentage_num)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _(
                    f"""The {'sales price' if self.apply_on == 'price' 
                    else 'cost'} is updated."""),
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class ChangePriceLine(models.TransientModel):
    _name = 'change.price.line'
    _rec_name = 'product_id'
    _description = "The Lines for Price and Cost Change"

    mass_price_update_id = fields.Many2one('mass.price.update', string='Number')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain="[('active', '=', True)]")
    current_price = fields.Float(string='Current Price', digits='Product Price',
                                 related='product_id.lst_price')
    new_price = fields.Float(string='New Price', digits='Product Price',
                             compute='_compute_new_price_cost')
    current_cost = fields.Float(string='Current Cost', digits='Product Price',
                                related='product_id.standard_price')
    new_cost = fields.Float(string='New Cost', digits='Product Price',
                            compute='_compute_new_price_cost')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', related='product_id.currency_id')

    @api.depends('mass_price_update_id.apply_on', 'mass_price_update_id.change',
                 'mass_price_update_id.apply_type')
    def _compute_new_price_cost(self):
        for record in self:
            if record.mass_price_update_id.apply_type == 'add':
                percentage_num = 1 + record.mass_price_update_id.change
            else:
                percentage_num = 1 - record.mass_price_update_id.change
            if record.mass_price_update_id.apply_on == 'price':
                record.new_cost = False
                record.new_price = record.current_price * percentage_num
            else:
                record.new_price = False
                record.new_cost = record.current_cost * percentage_num
