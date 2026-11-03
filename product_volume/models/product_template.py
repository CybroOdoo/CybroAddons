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

CUBIC_FEET_FACTOR = 35.3147

LENGTH_TO_M3_DIVISORS = {
    'meters': 1.0,
    'centimeters': 1000000.0,
    'inches': 61023.7,
    'feet': 35.3147,
    'yards': 1.308,
}

VOLUME_MULTIPLIERS = {
    'cubic_meters': 1.0,
    'cubic_inches': 61023.7,
    'cubic_feet': 35.3147,
    'cubic_yards': 1.308,
}


class ProductTemplate(models.Model):
    """Inherit product.template to add dimensions and volume calculation."""

    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._sync_dimension_volume()
        return templates

    def write(self, vals):
        dimensions_were_complete = {
            template.id: bool(
                template.length and template.breadth and template.height
            )
            for template in self
        }
        result = super().write(vals)
        if {'length', 'breadth', 'height', 'length_uom'} & vals.keys():
            self._sync_dimension_volume(
                clear_incomplete_ids={
                    template_id for template_id, complete
                    in dimensions_were_complete.items() if complete
                }
            )
        return result

    def _create_variant_ids(self):
        result = super()._create_variant_ids()
        self._sync_dimension_volume()
        return result

    def _sync_dimension_volume(self, clear_incomplete_ids=None):
        """Use dimensions for every variant when all dimensions are supplied.

        Incomplete dimensions leave a manually entered volume alone, except
        when dimensions were cleared after being complete. Core volume is
        expressed in the system UoM.
        """
        clear_incomplete_ids = clear_incomplete_ids or set()
        for template in self:
            vol_m3 = template._get_volume_in_m3()
            if not vol_m3 and template.id not in clear_incomplete_ids:
                continue
            system_volume = template._convert_m3_to_system_volume(vol_m3)
            variants = template.with_context(
                active_test=False
            ).product_variant_ids
            variants.volume = system_volume
            # Store the template value explicitly as well, so it is correct
            # for multi-variant templates without relying on core's compute.
            template.volume = system_volume

    @api.model
    def _resync_all_dimension_volumes(self):
        """Re-apply dimension volumes after the system volume unit changed.

        Variant volumes are stored in the system unit, so switching
        between cubic meters and cubic feet must convert every product
        whose volume is driven by its dimensions.
        """
        templates = self.sudo().with_context(active_test=False).search([
            ('length', '!=', 0),
            ('breadth', '!=', 0),
            ('height', '!=', 0),
        ])
        templates._sync_dimension_volume()

    length = fields.Float(  # pylint: disable=attribute-deprecated
        help="Enter length of the product",
    )
    breadth = fields.Float(
        help="Enter breadth of the product",
    )
    height = fields.Float(
        help="Enter height of the product",
    )
    length_uom = fields.Selection(
        selection=[
            ('meters', 'Meters'),
            ('centimeters', 'Centimeters'),
            ('inches', 'Inches'),
            ('feet', 'Feet'),
            ('yards', 'Yards'),
        ],
        string="UoM",
        default='meters',
        required=True,
        help="Select the unit of measure for length, breadth and height.",
    )

    @api.model
    def _is_volume_in_cubic_feet(self):
        """Check if the system volume unit is configured as cubic feet."""
        param = self.env['ir.config_parameter'].sudo().get_str(
            'product.volume_in_cubic_feet'
        )
        return param == '1'

    @api.model
    def _default_volume_uom(self):
        """Get the default volume unit based on system configuration."""
        if self._is_volume_in_cubic_feet():
            return 'cubic_feet'
        return 'cubic_meters'

    volume_uom = fields.Selection(
        selection=[
            ('cubic_meters', 'Cubic Meters'),
            ('cubic_inches', 'Cubic Inches'),
            ('cubic_feet', 'Cubic Feet'),
            ('cubic_yards', 'Cubic Yards'),
        ],
        string="UoM of Volume",
        default=lambda self: self._default_volume_uom(),
        required=True,
        help="Select the unit of measure for volume",
    )

    calc_volume = fields.Float(
        string="Calculated Volume",
        compute='_compute_calc_volume',
        digits='Volume',
        store=True,
        help="Volume calculated according to the selected unit of measure.",
    )

    def _get_volume_in_m3(self):
        """Calculate volume in cubic meters from product dimensions."""
        self.ensure_one()
        if not (self.length and self.breadth and self.height):
            return 0.0
        divisor = LENGTH_TO_M3_DIVISORS.get(self.length_uom, 1.0)
        return (self.length * self.breadth * self.height) / divisor

    def _convert_m3_to_system_volume(self, vol_m3):
        """Convert m³ volume to the system volume unit."""
        if self._is_volume_in_cubic_feet():
            return vol_m3 * CUBIC_FEET_FACTOR
        return vol_m3

    @api.depends('length', 'breadth', 'height', 'length_uom', 'volume_uom')
    def _compute_calc_volume(self):
        """Compute volume value according to the selected volume UoM."""
        for template in self:
            multiplier = VOLUME_MULTIPLIERS.get(template.volume_uom, 1.0)
            vol_m3 = template._get_volume_in_m3()
            if vol_m3:
                template.calc_volume = vol_m3 * multiplier
            else:
                template.calc_volume = 0.0
