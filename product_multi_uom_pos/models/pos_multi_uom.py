# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arwa V V (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class PosMultiUom(models.Model):
    """
    Model for managing Point of Sale (POS) Multi Unit of Measure (UoM).

    This model represents the association between a product template and its
    multiple unit of measure options for the Point of Sale module.
    """
    _name = 'pos.multi.uom'
    _description = 'POS Multi UoM'

    product_template_id = fields.Many2one('product.template',
                                          string='Product Template',
                                          help='Inverse field of one2many'
                                               'field POS Multiple UoM in'
                                               'product.template')
    category_id = fields.Many2one(
        related='product_template_id.uom_id.category_id',
        string='UoM Category', help='Category of unit of measure')
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure',
                             domain="[('category_id', '=', category_id)]",
                             help="Choose a UoM")
    price = fields.Float(string='Sale Price', help="Set a price for selected "
                                                   "UoM")
