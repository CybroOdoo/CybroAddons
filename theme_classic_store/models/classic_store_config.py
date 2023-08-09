# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import models, fields


class ClassicStoreConfig(models.Model):
    """Creating 'name', 'max_price', 'trending_product_ids', field in
    classic_store.config settings"""
    _name = 'classic_store.config'
    _description = 'Configuration Model For Theme Classic Store'

    name = fields.Char(string="Name",
                       help="Enter the name for the configuration.")
    max_price = fields.Integer(string="Maximum Price", default=100000,
                               help="Maximum amount to apply in "
                                    "product filter.")
    trending_product_ids = fields.Many2many('product.template',
                                            string="Trending Products",
                                            help="Manually enter trending "
                                                 "products or leave the field"
                                                 "blank to automatically "
                                                 "add the trending products.",
                                            domain=[
                                                ('is_published', '=', True)])
