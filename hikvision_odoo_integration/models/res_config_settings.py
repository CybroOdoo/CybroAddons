# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """Extends res.config.settings for Hikvision integration settings."""

    _inherit = 'res.config.settings'

    enable_hr_approval = fields.Boolean(
        string="HR Approval",
        config_parameter='hikvision_odoo_integration.enable_hr_approval'
    )

    minimum_working_hours = fields.Float(
        string="Minimum Working Hours",
        config_parameter='hikvision_odoo_integration.minimum_working_hours',
        default=8.0,
        help="Minimum working hours required per day without requiring approval"
    )

    def set_values(self):
        """Save settings and update menu visibility."""
        super(ResConfigSettings, self).set_values()
        self._update_attendance_approval_menu_visibility()

    def _update_attendance_approval_menu_visibility(self):
        """Update group membership to control menu visibility."""
        approval_group = self.env.ref('hikvision_odoo_integration.group_attendance_approval_menu',
                                      raise_if_not_found=False)
        if not approval_group:
            return

        if self.enable_hr_approval:
            all_users = self.env['res.users'].search([])
            approval_group.write({'users': [(4, user.id) for user in all_users]})
        else:
            approval_group.write({'users': [(5, 0, 0)]})
