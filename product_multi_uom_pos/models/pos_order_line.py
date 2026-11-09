# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (Contact : odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Product Unit',
        compute='_compute_product_uom_id',
        store=True,
        readonly=False,
        precompute=True,
        related=False,
    )
    custom_uom_name = fields.Char(string='Custom UoM Name')
    custom_uom_price = fields.Float(string='Custom UoM Price')

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            if not line.product_uom_id:
                line.product_uom_id = line.product_id.uom_id

    @api.model
    def _load_pos_data_fields(self, config):
        """Include custom UoM fields when loading order lines in POS."""
        params = super()._load_pos_data_fields(config)
        params += ['custom_uom_name', 'custom_uom_price', 'product_uom_id']
        return params
