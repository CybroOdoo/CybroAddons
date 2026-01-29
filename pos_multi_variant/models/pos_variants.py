# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreejith sasidharan(<https://www.cybrosys.com>)
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
from odoo import api, models, fields


class PosVarients(models.Model):

    _inherit = ['product.template']

    pos_variants = fields.Boolean('pos variants', default=False)
    variant_line_ids = fields.One2many('variants.tree', 'variants_id', string="Configure Variants")


class VariantsSelection(models.Model):

    _name = 'variants.tree'

    variants_id = fields.Many2one('product.template')
    attribute = fields.Many2one('product.attribute', string='Attribute', ondelete='restrict', required=True, index=True)
    value = fields.Many2many('product.attribute.value', string='Values')
    extra_price = fields.Float(string="Price Extra")
    pos_active = fields.Boolean(string="Active")


