# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extends Settings with waste management configuration parameters and default locations."""
    _inherit = 'res.config.settings'

    group_wm_audit_trail = fields.Boolean(string="Enable Audit Trail", implied_group="wm_base.group_wm_audit_trail", config_parameter="wm_base.group_wm_audit_trail")
    module_wm_recycling = fields.Boolean(
        string="Recycling",
        help="Install and enable recycling orders, material recovery tracking, and yield analysis."
    )
    module_wm_compliance = fields.Boolean(
        string="Compliance Management",
        help="Install and enable regulatory tracking, hazardous waste manifests, chain of custody, and compliance certificates."
    )

    def get_values(self):
        """
        Load current configuration values from
        ir.config_parameter and populate the settings form so users see the
        active system configuration.
        """
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo().get_param('wm_base.group_wm_audit_trail', default='False')
        res.update(
            group_wm_audit_trail=str(param).lower() in ('true', '1', 'yes'),
        )
        return res

    def set_values(self):
        """
        Persist all configuration values (default locations,
        billing thresholds, weight tolerances) to ir.config_parameter when
        settings are saved.
        """
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'wm_base.group_wm_audit_trail',
            'True' if self.group_wm_audit_trail else 'False'
        )
        menu_audit = self.env.ref('wm_base.menu_wm_audit_trail', raise_if_not_found=False)
        if menu_audit:
            menu_audit.active = bool(self.group_wm_audit_trail)
        menu_logs = self.env.ref('wm_base.menu_wm_audit_logs', raise_if_not_found=False)
        if menu_logs:
            menu_logs.active = bool(self.group_wm_audit_trail)
        menu_transitions = self.env.ref('wm_base.menu_wm_status_transitions', raise_if_not_found=False)
        if menu_transitions:
            menu_transitions.active = bool(self.group_wm_audit_trail)
