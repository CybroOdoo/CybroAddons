# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Adds the session expiry setting to the general settings."""
    _inherit = 'res.config.settings'

    session_expire_time = fields.Integer(
        'Session Expire time In Minutes',
        config_parameter='restrict_logins.session_expire_time',
        default=10,
        help="Minutes of inactivity after which a user session expires.")

    @api.constrains('session_expire_time')
    def _check_session_expire_time(self):
        """A session must last at least one minute."""
        for settings in self:
            if settings.session_expire_time < 1:
                raise ValidationError(self.env._(
                    "The session expiry time must be at least 1 minute."))
