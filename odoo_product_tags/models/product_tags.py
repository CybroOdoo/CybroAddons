# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from random import randint


class ProductTags(models.Model):
    _name = "product.tags"
    _description = 'Product Tags'
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _random_color(self):
        return randint(1, 11)

    name = fields.Char(required=1, copy=False, string='Name')
    description = fields.Text(string='Description', translate=True)
    tag_color = fields.Integer(string="Tag Color", default=_random_color)
    product_tmpl_ids = fields.Many2many('product.template', string="Products")

