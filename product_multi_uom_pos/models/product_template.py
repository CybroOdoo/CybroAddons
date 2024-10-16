# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (Contact : odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """Inherits model 'product.template' and adds field to set multiple units
    of measure"""
    _inherit = 'product.template'

    product_uom_category_id = fields.Many2one(related='uom_id.category_id')
    pos_multi_uom_ids = fields.Many2many('uom.uom', 'product_template_id',
                                        string="POS Multiple UoM",
                                        domain="[('category_id', '=', product_uom_category_id)]",
                                        help='These UoM can be selected from '
                                             'PoS')