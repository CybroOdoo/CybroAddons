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


class Users(models.Model):
    """Inherit and add idle timeout fields to res.users."""
    _inherit = "res.users"

    enable_idle = fields.Boolean(
        string="Enable Idle Timeout",
        help="Enable automatic session logout after inactivity for this user.",
    )
    idle_time = fields.Float(
        string="Idle Time (Minutes)",
        default=15.0,
        help="Inactivity period in minutes before the user is automatically logged out.",
    )

    @api.constrains('enable_idle', 'idle_time')
    def _check_idle_time(self):
        """Ensure the idle time is at least one minute when enabled."""
        for user in self:
            if user.enable_idle and user.idle_time < 1.0:
                raise ValidationError(self.env._(
                    "Idle Time must be at least 1 minute when the idle "
                    "timeout is enabled."))
