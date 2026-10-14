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
#############################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

# Palette replacement assets (blue is the default palette, no asset needed).
THEME_ASSETS = {
    'green': 'vista_backend_theme.vista_theme_palette_green',
    'black': 'vista_backend_theme.vista_theme_palette_black',
}

# Icon set used by each theme (folder inside static/src/img).
THEME_ICON_FOLDERS = {
    'blue': 'icons',
    'green': 'icons_green',
    'black': 'icons',
}

# Root menu name (English) -> icon file.
MENU_ICONS = {
    'Contacts': 'contacts.png',
    'Link Tracker': 'link-tracker.png',
    'Dashboards': 'dashboards.png',
    'Sales': 'sales.png',
    'Invoicing': 'accounting.png',
    'Accounting': 'accounting.png',
    'Inventory': 'inventory.png',
    'Purchase': 'purchase.png',
    'Calendar': 'calendar.png',
    'CRM': 'crm.png',
    'Note': 'notes.png',
    'Notes': 'notes.png',
    'Documents': 'documents.png',
    'Planning': 'planning.png',
    'Services': 'services.png',
    'Website': 'website.png',
    'Point of Sale': 'pos.png',
    'Manufacturing': 'manufacturing.png',
    'Repairs': 'repairs.png',
    'Email Marketing': 'email-marketing.png',
    'SMS Marketing': 'sms-marketing.png',
    'Project': 'project.png',
    'Surveys': 'surveys.png',
    'Employees': 'employee.png',
    'Recruitment': 'recruitment.png',
    'Attendances': 'attendance.png',
    'Time Off': 'timeoff.png',
    'Expenses': 'expenses.png',
    'Maintenance': 'maintenance.png',
    'Live Chat': 'live-chat.png',
    'Lunch': 'lunch.png',
    'Fleet': 'fleet.png',
    'Timesheets': 'timesheet.png',
    'Events': 'events.png',
    'eLearning': 'elearning.png',
    'Members': 'members.png',
    'Apps': 'apps.png',
    'Discuss': 'discuss.png',
    'Settings': 'settinga.png',
}


class ThemeData(models.TransientModel):
    """Wizard used to pick the backend theme."""
    _name = "theme.data"
    _description = "Theme Data Wizard"

    @api.model
    def _get_current_theme(self):
        """The active theme is the one whose palette asset is active."""
        for theme, xmlid in THEME_ASSETS.items():
            asset = self.env.ref(xmlid, raise_if_not_found=False)
            if asset and asset.sudo().active:
                return theme
        return 'blue'

    name = fields.Selection([
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('black', 'Black'),
    ], string='Theme', required=True, default=lambda self: self._get_current_theme())

    @api.model
    def set_theme(self, theme):
        """Activate ``theme`` (asset palette + menu icons). Admins only."""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._("Only administrators can change the backend theme."))
        if theme not in THEME_ICON_FOLDERS:
            return False
        for theme_name, xmlid in THEME_ASSETS.items():
            asset = self.env.ref(xmlid, raise_if_not_found=False)
            if asset:
                asset.sudo().active = theme_name == theme
        self._apply_menu_icons(theme)
        return True

    def action_apply(self):
        self.ensure_one()
        self.set_theme(self.name)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def _apply_menu_icons(self, theme):
        """Set the icons of the root menus (apps) for ``theme``."""
        folder = THEME_ICON_FOLDERS[theme]
        menus = self.env['ir.ui.menu'].sudo().with_context(lang='en_US').search(
            [('parent_id', '=', False)])
        for menu in menus:
            icon = MENU_ICONS.get((menu.name or '').strip())
            if not icon:
                continue
            image = menu._read_image(f'vista_backend_theme,static/src/img/{folder}/{icon}')
            if image:
                menu.web_icon_data = image
            else:
                _logger.warning("Icon %s/%s not found for menu %s", folder, icon, menu.name)

    @api.model
    def _restore_menu_icons(self):
        """Give back to the root menus the icon declared by their web_icon."""
        menus = self.env['ir.ui.menu'].sudo().search([('parent_id', '=', False)])
        for menu in menus:
            menu.web_icon_data = menu._compute_web_icon_data(menu.web_icon)
