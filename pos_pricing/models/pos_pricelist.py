# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Linto C T(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields


class PosPriceList(models.Model):
    _name = 'pos.pricelist'

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string="Name", required=True)
    item_ids = fields.One2many('pos.pricelist.items', 'pos_pricelist_id', string="Pricelist Items")
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    company_id = fields.Many2one('res.company', 'Company')


class PosPricelistItems(models.Model):
    _name = 'pos.pricelist.items'

    name = fields.Char(string="Name", required=True)
    pos_pricelist_id = fields.Many2one('pos.pricelist', string="Pricelist")
    applied_on = fields.Selection([('global', "Global"), ('product_category', 'Product Category'),
                                   ('product', 'Product')], string="Applied On", default='global', required=True)
    min_quantity = fields.Integer(string="Minimum Quantity")
    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")
    compute_price = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')],
                                     string="Compute Price", default='fixed')
    fixed_price = fields.Float(string="Fixed Price")
    percent_price = fields.Float(string="Percentage")

    categ_id = fields.Many2one('pos.category', string="POS Product Category")
    product_tmpl_id = fields.Many2one('product.template', string="Product")

    company_id = fields.Many2one('res.company', 'Company', readonly=True, related='pos_pricelist_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  readonly=True, related='pos_pricelist_id.currency_id', store=True)


class PriceListPartner(models.Model):
    _inherit = 'res.partner'

    pos_pricelist_id = fields.Many2one('pos.pricelist', string="POS Pricelist")