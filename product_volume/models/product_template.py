# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models, fields


class ProductDimensionsVolume(models.Model):
    """Inheriting product_template to add new fields"""
    _inherit = 'product.template'

    length = fields.Char(string="Length", help="Enter length of the product")
    breadth = fields.Char(string="Breadth", help="Enter breadth of the product")
    height = fields.Char(string="Height", help="Enter height of the product")
    length_uom = fields.Selection(
        selection=[('meters', 'Meters'), ('centimeters', 'Centimeters'),
                   ('inches', 'Inches'), ('feet', 'Feet'), ('yards', 'Yards')],
        string="UoM", default='meters', required=True,
        help="Select the unit of measure for length and")
    volume_uom = fields.Selection(
        selection=[('cubic_meters', 'Cubic Meters'),
                   ('cubic_inches', 'Cubic Inches'),
                   ('cubic_feet', 'Cubic Feet'),
                   ('cubic_yards', 'Cubic Yards')],
        string="UoM of Volume", default='cubic_meters', required=True,
        help="Select the unit of measure for volume")

    @api.onchange('length', 'breadth', 'height', 'length_uom', 'volume_uom')
    def _onchange_product_measures(self):
        """Onchange function to calculate volume of the product"""
        volume = 0
        if self.length_uom == "meters":
            volume = (float(self.length if self.length else 0) *
                      float(self.breadth if self.breadth else 0) * float(
                        self.height if self.height else 0))
        elif self.length_uom == "centimeters":
            volume = ((float(self.length if self.length else 0) * float(
                self.breadth if self.breadth else 0) * float(
                self.height if self.height else 0)) / 1000000)
        elif self.length_uom == "inches":
            volume = ((float(self.length if self.length else 0) *
                       float(self.breadth if self.breadth else 0) *
                       float(self.height if self.height else 0)) / 61023.7)
        elif self.length_uom == "feet":
            volume = ((float(self.length if self.length else 0) *
                       float(self.breadth if self.breadth else 0) *
                       float(self.height if self.height else 0)) / 35.3147)
        elif self.length_uom == "yards":
            volume = ((float(self.length or 0) * float(
                self.breadth or 0) * float(self.height or 0)) / 1.308)
        if self.volume_uom == 'cubic_meters':
            self.volume = volume
        if self.volume_uom == 'cubic_inches':
            self.volume = volume * 61023.7
        if self.volume_uom == 'cubic_feet':
            self.volume = volume * 35.3147
        if self.volume_uom == 'cubic_yards':
            self.volume = volume * 1.308
