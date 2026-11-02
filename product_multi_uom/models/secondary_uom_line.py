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
from odoo.exceptions import ValidationError


class SecondaryUomLine(models.Model):
    """Model Class for Secondary Uom Line
    This class represents the secondary unit of measure (UOM) line in the
    system.
    It is designed to store information related to secondary UOMs."""
    _name = "secondary.uom.line"
    _description = "Secondary Uom Line"

    secondary_uom_id = fields.Many2one('uom.uom', string='Secondary UoM',
                                       help="Select the Secondary UoM",
                                       required=True)
    product_id = fields.Many2one('product.product', readonly=True,
                                 help="Product having the Secondary UOM")
    product_template_id = fields.Many2one('product.template', readonly=True,
                                          string="Product",
                                          help="Product having the Secondary UOM")
    secondary_uom_ratio = fields.Float(string='Secondary UoM Ratio',
                                       help="Choose the ratio with the base"
                                            " Unit of Measure.")
    example_ratio = fields.Char(string='Ratio', readonly=True,
                                help="Ratio of base Uom and the secondary Uom",
                                store=True)
    uom_ids = fields.Many2many('uom.uom', string='Uom_ids', compute='_compute_uom_ids')

    @api.depends('secondary_uom_id', 'product_id', 'product_template_id')
    def _compute_uom_ids(self):
        """
            Compute available UoM records based on the parent UoM from context,
            excluding already selected UoMs, and assign them to the record.
            """
        for rec in self:
            uom_ids = self.env['uom.uom'].sudo().search(
                ['|', ('relative_uom_id', 'in', [self.env.context.get('parent_uom_id')]),
                 ('id', '=', self.env.context.get('parent_uom_id')),
                 ('id', 'not in', self.env.context.get('selected_uom_ids', []))
                 ])
            rec.uom_ids = [fields.Command.set(uom_ids.ids)]

    @api.onchange('secondary_uom_id')
    def _onchange_secondary_uom_id(self):
        """Default the ratio to the UoM's relative factor when selected."""
        if self.secondary_uom_id:
            self.secondary_uom_ratio = self.secondary_uom_id.relative_factor

    @api.onchange('secondary_uom_id', 'secondary_uom_ratio')
    def _onchange_secondary_uom_ratio(self):
        """Update the example ratio display when UoM or custom ratio changes."""
        if self.secondary_uom_id and self.secondary_uom_ratio:
            base_name = self.product_id.uom_id.name or self.product_template_id.uom_id.name or ''
            self.example_ratio = f"1 {self.secondary_uom_id.name} = {self.secondary_uom_ratio} {base_name}".strip()

    @api.constrains('secondary_uom_id', 'product_id', 'product_template_id')
    def _check_unique_secondary_uom(self):
        """Ensure secondary UoM is unique per product or product template."""
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('secondary_uom_id', '=', rec.secondary_uom_id.id),
            ]
            if rec.product_id:
                domain.append(('product_id', '=', rec.product_id.id))
            elif rec.product_template_id:
                domain.append(('product_template_id', '=', rec.product_template_id.id))
            else:
                continue
            if self.search_count(domain):
                raise ValidationError(
                    self.env._('This Unit of Measure already exists in the secondary '
                               'UoM list. Please select another UoM.')
                )
