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
    """Extends Settings with waste collection workflow parameters and dispatch rules."""
    _inherit = 'res.config.settings'

    wm_auto_dispatch_enabled = fields.Boolean(
        string="Enable Auto-Dispatch of Ready Routes",
        config_parameter='wm_collection.auto_dispatch_enabled',
        default=False,
        help=(
            "When enabled, the hourly cron will automatically dispatch any "
            "route that is fully staffed (vehicle, driver, pre-trip checklist) "
            "and whose linked collection orders are all complete.\n\n"
            "When disabled the cron still evaluates readiness and sets the "
            "'Ready to Dispatch' flag on the route, but a human dispatcher "
            "must press Dispatch Route manually."
        ),
    )
    use_missed_collection = fields.Boolean(
        string="Enable Missed Collections",
        config_parameter='wm_collection.use_missed_collection',
        help="Enable missed collection tracking, reason management, and retry workflows."
    )
    use_route_zones = fields.Boolean(
        string="Route Service Zones & Auto-Assignment",
        config_parameter='wm_collection.use_route_zones',
        help="Enable geographic service zones and daily automated assignment of collection orders to zoned routes."
    )

    def get_values(self):
        """
        Load all collection module configuration parameters from
        ir.config_parameter into the settings form, ensuring operators see the
        currently active collection workflow options.
        """
        res = super(ResConfigSettings, self).get_values()
        val_missed = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_missed_collection', default='True')
        val_zones = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_route_zones', default='True')
        res.update(
            use_missed_collection=val_missed in ('True', '1', True),
            use_route_zones=val_zones in ('True', '1', True),
        )
        return res

    def set_values(self):
        """
        Persist all collection module settings (batch defaults, zone
        restrictions, driver signature requirements) to ir.config_parameter
        when the user saves the settings form.
        """
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'wm_collection.use_missed_collection',
            'True' if self.use_missed_collection else 'False'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'wm_collection.use_route_zones',
            'True' if self.use_route_zones else 'False'
        )
        menu_missed = self.env.ref('wm_collection.menu_wm_missed_collection', raise_if_not_found=False)
        if menu_missed:
            menu_missed.active = self.use_missed_collection

        menu_reason = self.env.ref('wm_collection.menu_wm_missed_reason', raise_if_not_found=False)
        if menu_reason:
            menu_reason.active = self.use_missed_collection

        menu_zone = self.env.ref('wm_collection.menu_wm_service_zone', raise_if_not_found=False)
        if menu_zone:
            menu_zone.active = self.use_route_zones

        # Sync scheduled action active status with settings
        cron_assign = self.env.ref('wm_collection.ir_cron_auto_assign_orders_to_routes', raise_if_not_found=False)
        if cron_assign:
            cron_assign.active = self.use_route_zones

        cron_dispatch = self.env.ref('wm_collection.ir_cron_auto_dispatch_ready_routes', raise_if_not_found=False)
        if cron_dispatch:
            cron_dispatch.active = self.wm_auto_dispatch_enabled

        cron_missed = self.env.ref('wm_collection.ir_cron_wm_missed_collection_weekly_review', raise_if_not_found=False)
        if cron_missed:
            cron_missed.active = self.use_missed_collection
