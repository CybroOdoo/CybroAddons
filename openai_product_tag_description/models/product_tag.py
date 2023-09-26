# -*- coding:utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from random import randint
from odoo import fields, models


class ProductTag(models.Model):
    """Create a model to assign tags for products"""
    _name = 'product.tag'
    _description = 'Product Tag'

    def add_random_color(self):
        """Summary:
              Function to set default colour for tags
                      """
        return randint(1, 11)

    name = fields.Char(required=1, copy=False, string='Name',
                       help='Name of tag')
    tag_color = fields.Integer(string="Tag Color", default=add_random_color,
                               help='Colour of tag')
