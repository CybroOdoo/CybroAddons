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
    """Extends Settings with the audit trail toggle and optional waste management add-on switches."""
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
    module_wm_subscription = fields.Boolean(
        string="Subscriptions",
        help="Install and enable customer subscription management, recurring billing, and monthly weight allowance quotas."
    )
    module_wm_driver_app = fields.Boolean(
        string="Driver Mobile App",
        help="Install and enable the offline-first driver PWA mobile app, stop status progression, GPS verification, and driver checklists."
    )

    def get_values(self):
        """
        Load current configuration values from
        ir.config_parameter and populate the settings form so users see the
        active system configuration.
        """
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo().get_param('wm_base.group_wm_audit_trail', default='False')
        res.update(
            group_wm_audit_trail=str(param).lower() in ('true', '1', 'yes'),
        )
        return res

    def set_values(self):
        """
        Persist the audit trail switch to ir.config_parameter and show or
        hide the audit menus accordingly when settings are saved.
        """
        res = super().set_values()
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
        return res
