# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models,fields, api, _


class SilonConfiguration(models.Model):
    _name = 'silon.configuration'

    name = fields.Char('Name')
    featured_product_ids = fields.Many2many('product.product')


class Product(models.Model):
    _inherit = 'product.template'

    qty_sold = fields.Integer('Quantity sold')
    views = fields.Integer('Views')
    top_selling = fields.Boolean('TopSelling')
    most_viewed = fields.Boolean('Most Viewed')
