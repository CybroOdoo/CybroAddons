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
from odoo import api, models

VOLUME_UNIT_PARAM = 'product.volume_in_cubic_feet'


class IrConfigParameter(models.Model):
    """Re-sync dimension-based volumes when the system volume unit changes."""

    _inherit = 'ir.config_parameter'

    def _volume_in_cubic_feet_state(self):
        """Return whether the system volume unit is currently cubic feet."""
        return self.env['product.template']._is_volume_in_cubic_feet()

    def _resync_if_volume_unit_changed(self, was_cubic_feet):
        """Convert stored volumes when the volume unit parameter changed."""
        if self._volume_in_cubic_feet_state() != was_cubic_feet:
            self.env['product.template']._resync_all_dimension_volumes()

    @api.model_create_multi
    def create(self, vals_list):
        touches_unit = any(
            vals.get('key') == VOLUME_UNIT_PARAM for vals in vals_list
        )
        was_cubic_feet = touches_unit and self._volume_in_cubic_feet_state()
        records = super().create(vals_list)
        if touches_unit:
            self._resync_if_volume_unit_changed(was_cubic_feet)
        return records

    def write(self, vals):
        touches_unit = (
            vals.get('key') == VOLUME_UNIT_PARAM
            or VOLUME_UNIT_PARAM in self.mapped('key')
        )
        was_cubic_feet = touches_unit and self._volume_in_cubic_feet_state()
        result = super().write(vals)
        if touches_unit:
            self._resync_if_volume_unit_changed(was_cubic_feet)
        return result

    def unlink(self):
        touches_unit = VOLUME_UNIT_PARAM in self.mapped('key')
        was_cubic_feet = touches_unit and self._volume_in_cubic_feet_state()
        result = super().unlink()
        if touches_unit:
            self._resync_if_volume_unit_changed(was_cubic_feet)
        return result
