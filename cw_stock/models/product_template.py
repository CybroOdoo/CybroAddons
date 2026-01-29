# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
    """Inherit product template to include Catch Weight fields"""
    _inherit = 'product.template'

    apply_cw = fields.Boolean(string='CW Product',
                              help="True for Catch Weight Products")
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                store=True,
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    catch_weight_ok = fields.Boolean(default=False,
                                     string="Catch Weight Product",
                                     help="True for catch weight products")
    average_cw_qty = fields.Float(string='Catch Weight', digits=(16, 4),
                                  default=1.0, help="Catch weight quantity")
