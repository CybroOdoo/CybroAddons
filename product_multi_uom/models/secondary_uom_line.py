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
                                 string="Product",
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

    @api.onchange('secondary_uom_id', 'secondary_uom_ratio')
    def _onchange_secondary_uom_id(self):
        """Function that write the ratio in to the example ratio field and
         check whether the selected secondary uom is already included in the
         uom list"""
        self.secondary_uom_ratio = self.secondary_uom_id.relative_factor
        if self.secondary_uom_id and self.secondary_uom_ratio:
            self.example_ratio = (f" 1 {self.secondary_uom_id.name}  = "
                                  f" {self.secondary_uom_ratio} "
                                  f"{self.product_id.uom_id.name or self.product_template_id.uom_id.name}")
        if self.env.context.get('params'):
            sec_uom_ids = self.env['product.product'].browse(
                self.env.context.get('params').get('id')).secondary_uom_ids.mapped(
                'secondary_uom_id.id')
            if self.secondary_uom_id.id in sec_uom_ids:
                raise ValidationError(
                    self.env._('This Unit of Measure is already exist in the secondary'
                               'uom list. Please select another uom for secondary uom'))
