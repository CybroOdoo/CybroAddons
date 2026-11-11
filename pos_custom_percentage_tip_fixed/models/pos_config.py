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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfiguration(models.Model):
    """Inheriting pos.config to add custom tip percentage configuration."""

    _inherit = 'pos.config'

    custom_tip_percentage = fields.Float(
        string="Custom Percentage",
        help="Enter the percentage custom tips",
    )

    @api.constrains('custom_tip_percentage')
    def _check_custom_tip_percentage(self):
        """Validate that custom tip percentage is between 0 and 100."""
        for record in self:
            if not 0.0 <= record.custom_tip_percentage <= 100.0:
                raise ValidationError(
                    _("Custom tip percentage must be between 0 and 100."),
                )
