# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (<https://www.cybrosys.com>)
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


class ProductTemplate(models.Model):
    """Inherits the 'product.template' for adding the secondary uom"""
    _inherit = "product.template"

    is_need_secondary_uom = fields.Boolean(string="Need Secondary UoM's",
                                           help="Enable this field for "
                                                "using the secondary uom")
    secondary_uom_ids = fields.One2many('secondary.uom.line', 'product_template_id',
                                        string="Secondary UoM's",
                                        help='Select the secondary UoM and '
                                             'their ratio', store=True)

    selected_uom_ids = fields.Many2many('uom.uom', help='Chosen Uom in the secondly uom',
                                        string='Selected Uom Ids', compute='_compute_selected_uom_ids')

    @api.depends('secondary_uom_ids')
    def _compute_selected_uom_ids(self):
        """ Compute selected uom ids to set domain"""
        for rec in self:
            rec.selected_uom_ids = [fields.Command.set(rec.secondary_uom_ids.mapped('secondary_uom_id.id'))]

    @api.onchange('is_need_secondary_uom', 'uom_id')
    def _onchange_is_need_secondary_uom(self):
        """Function that write the default Uom and their ratio to the
        secondary uom"""
        self.secondary_uom_ids = [fields.Command.clear()]
        base_uom = self.env['uom.uom'].sudo().search(
            ['|', ('relative_uom_id', '=', [self.uom_id.id]),
             ('id', '=', self.uom_id.id)])
        if not self.secondary_uom_ids or self.uom_id.id not in self.secondary_uom_ids.mapped('secondary_uom_id').ids:
            for uom in base_uom:
                self.write({
                    'secondary_uom_ids': [fields.Command.create({
                        'secondary_uom_id': uom.id,
                        'secondary_uom_ratio': float(uom.relative_factor),
                        'example_ratio': f" 1 {uom.name} = {uom.relative_factor}"
                                         f" {self.uom_id.name}",
                    })]
                })

    @api.model_create_multi
    def create(self, vals_list):
        """Assign default value to the product variants"""
        res = super().create(vals_list)
        for product in res:
            if product.is_need_secondary_uom:
                product.product_variant_ids.is_need_secondary_uom = True
        return res
