# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProductProduct(models.Model):
    """Inherits the 'product.template' for adding the secondary uom"""
    _inherit = "product.product"

    is_need_secondary_uom = fields.Boolean(string="Need Secondary UoM's",
                                           help="Enable this field for "
                                                "using the secondary uom")
    secondary_uom_ids = fields.One2many('secondary.uom.line', 'product_id',
                                        string="Secondary UoM's",
                                        help='Select the secondary UoM and '
                                             'their ratio', store=True)

    @api.onchange('is_need_secondary_uom')
    def _onchange_is_need_secondary_uom(self):
        """Function that write the default Uom and their ratio to the
        secondary uom"""
        base_uom = self.env['uom.uom'].sudo().search(
                [('category_id', '=', self.uom_id.category_id.id)])
        if not self.secondary_uom_ids:
            for uom in base_uom:
                self.write({
                    'secondary_uom_ids': [(0, 0, {
                        'secondary_uom_id': uom.id,
                        'secondary_uom_ratio': float(uom.factor_inv),
                        'example_ratio': f" 1 {uom.name} = {uom.factor_inv}"
                                         f" {self.uom_id.name}",
                    })]
                })
