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
from odoo import api, fields, models, _
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
    secondary_uom_ratio = fields.Float(string='Secondary UoM Ratio',
                                       help="Choose the ratio with the base"
                                            " Unit of Measure.")
    example_ratio = fields.Char(string='Ratio', readonly=True,
                                help="Ratio of base Uom and the secondary Uom",
                                store=True)

    @api.onchange('secondary_uom_id', 'secondary_uom_ratio')
    def _onchange_secondary_uom_id(self):
        """Function that write the ratio in to the example ratio field and
         check whether the selected secondary uom is already included in the
         uom list"""
        if self.secondary_uom_id and self.secondary_uom_ratio:
            self.example_ratio = (f" 1 {self.secondary_uom_id.name}  = "
                                  f" {self.secondary_uom_ratio} "
                                  f"{self.product_id.uom_id.name}")
        if self._context.get('params'):
            sec_uom_ids = self.env['product.template'].browse(
                self._context.get('params').get('id')).secondary_uom_ids.mapped(
                'secondary_uom_id.id')
            if self.secondary_uom_id.id in sec_uom_ids:
                raise ValidationError(
                    _('This Unit of Measure is already exist in the secondary '
                      'uom list. Please select another uom for secondary uom'))
