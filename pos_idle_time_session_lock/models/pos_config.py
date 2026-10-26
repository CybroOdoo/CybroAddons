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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    """Set the lock and time limit for the session lock configuration."""

    _inherit = 'pos.config'

    pos_lock = fields.Boolean(
        string='Enable Lock Screen',
        help='Automatically lock the POS screen after a period of inactivity.'
    )
    idle_time_limit = fields.Integer(
        string="Idle Time Limit (In Minutes)",
        default=10,
        help='Idle timeout in minutes before automatically locking the screen.'
    )

    @api.constrains('pos_lock', 'idle_time_limit')
    def _check_idle_time_limit(self):
        """Ensure idle time limit is positive when lock is enabled."""
        for config in self:
            if config.pos_lock and config.idle_time_limit <= 0:
                raise ValidationError(
                    "Idle time limit must be greater than zero minutes."
                )
