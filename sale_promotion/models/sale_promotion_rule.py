# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import UserError
from odoo import models, fields, _, api


class SalePromotion(models.Model):
    _name = 'sale.promotion'

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string="Name", required=True)
    item_ids = fields.One2many('sale.promotion.rule', 'promotion_id', string="Promotion Rules")
    company_id = fields.Many2one('res.company')
    currency_id = fields.Many2one('res.currency')


class SalePromotionRule(models.Model):
    _name = 'sale.promotion.rule'

    name = fields.Char(string="Name", required=True)
    promotion_id = fields.Many2one('sale.promotion', string="Promotion Rule")
    applied_on = fields.Selection([('product_category', 'Product Category'),
                                   ('product', 'Product')], string="Applied On", default='product', required=True)
    min_quantity = fields.Integer(string="Minimum Quantity")
    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")
    categ_id = fields.Many2one('product.category', string="Product Category")
    product_tmpl_id = fields.Many2one('product.product', string="Product")

    company_id = fields.Many2one('res.company', string='Company', readonly=True, related='promotion_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True, related='promotion_id.currency_id', store=True)
    promotion_rule_lines = fields.One2many('sale.promotion.rule.line', 'promotion_rule_id', string="Promotion Lines")

    @api.constrains('date_start', 'date_end')
    def check_date(self):
        if self.date_start and self.date_end:
            if self.date_end < self.date_start:
                raise UserError(_('Please check the Ending date.'))

    @api.constrains('promotion_rule_lines')
    def check_promotion(self):
        if not self.promotion_rule_lines:
            raise UserError(_('Please Add some promotion products.'))


class SalePromotionLines(models.Model):
    _name = 'sale.promotion.rule.line'

    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Integer(string="Quantity")
    promotion_rule_id = fields.Many2one('sale.promotion.rule', string="Promotion Lines")






