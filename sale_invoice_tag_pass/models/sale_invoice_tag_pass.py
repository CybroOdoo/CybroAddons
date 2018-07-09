# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
from odoo import models, api, fields


class SaleTag(models.Model):
    _inherit = 'sale.order'

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    sale_tag = fields.Many2many('res.partner.category', column1='partner_id',
                                column2='category_id', string='Sales Tag', default=_default_category)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    check_sale_tag = fields.Boolean()
    sale_tag = fields.Many2many('res.partner.category', column1='partner_id',
                                column2='category_id', string='Sales Tag', compute='get_sales_tag')

    @api.one
    @api.depends('user_id')
    def get_sales_tag(self):
        if self.name:
            sale_order = self.env['sale.order']
            sale_tags = sale_order.search([('name', '=', self.name)])
            for tag in sale_tags:
                self.sale_tag = tag.sale_tag





