# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    """Inherits the 'product.template' for adding the secondary uom"""
    _inherit = "product.product"

    is_need_secondary_uom = fields.Boolean(string="Need Secondary UoMs",
                                           help="Enable this field for "
                                                "using the secondary uom")
    secondary_uom_ids = fields.One2many('secondary.uom.line', 'product_id',
                                        string="Secondary UoMs",
                                        help='Select the secondary UoM and '
                                             'their ratio', store=True)
    selected_uom_ids = fields.Many2many('uom.uom', help='Chosen UoMs in secondary UoMs',
                                        string='Selected Uom Ids', compute='_compute_selected_uom_ids')

    @api.depends('secondary_uom_ids')
    def _compute_selected_uom_ids(self):
        """ Compute selected uom ids to set domain"""
        for rec in self:
            rec.selected_uom_ids = [fields.Command.set(rec.secondary_uom_ids.mapped('secondary_uom_id.id'))]

    @api.onchange('is_need_secondary_uom', 'uom_id')
    def _onchange_is_need_secondary_uom(self):
        """Write default UoMs and their ratio to the secondary UoMs."""
        self.secondary_uom_ids = [fields.Command.clear()]
        if not self.is_need_secondary_uom:
            return
        base_uom = self.env['uom.uom'].sudo().search(
            ['|', ('relative_uom_id', 'in', [self.uom_id.id]),
             ('id', '=', self.uom_id.id)])
        for uom in base_uom:
            self.write({
                'secondary_uom_ids': [fields.Command.create({
                    'secondary_uom_id': uom.id,
                    'secondary_uom_ratio': float(uom.relative_factor),
                    'example_ratio': f"1 {uom.name} = {uom.relative_factor} {self.uom_id.name}",
                })]
            })

    @api.model_create_multi
    def create(self, vals_list):
        """Assign default values to secondary UoMs when enabled."""
        res = super().create(vals_list)
        for rec in res:
            if rec.is_need_secondary_uom:
                rec._onchange_is_need_secondary_uom()
        return res
