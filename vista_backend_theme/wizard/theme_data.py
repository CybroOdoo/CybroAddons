# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
import logging
from odoo import api, fields, models
import odoo.tools.misc

_logger = logging.getLogger(__name__)


class ThemeData(models.TransientModel):
    """Wizard for theme selection"""
    _name = "theme.data"
    _description = "Theme Data Wizard"

    def _get_current_theme(self):
        """Get the current active theme"""
        theme = self.env['theme.data.stored'].sudo().search([], limit=1)
        return theme.name if theme else 'default'

    name = fields.Selection([
        ('default', 'Default'),
        ('two', 'Green'),
        ('three', 'Black'),
    ], 'Theme', required=True, default=_get_current_theme)

    @api.onchange('name')
    def _onchange_name(self):
        """Update theme when selection changes"""
        theme = self.sudo().env.ref('vista_backend_theme.theme_data_stored', raise_if_not_found=False)
        if theme:
            theme.name = self.name
        else:
            self.env['theme.data.stored'].sudo().create({'name': self.name})

    def action_apply(self):
        """Apply the selected theme"""
        name = self.env['theme.data.stored'].sudo().search([], limit=1).name

        # Deactivate all theme CSS files first
        theme_refs = {
            'green_css': 'vista_backend_theme.vista_theme_css_green',
            'green_login': 'vista_backend_theme.vista_theme_css_login_green',
            'black_css': 'vista_backend_theme.vista_theme_css_black',
            'black_login': 'vista_backend_theme.vista_theme_css_login_black',
        }

        for ref in theme_refs.values():
            asset = self.env.ref(ref, raise_if_not_found=False)
            if asset:
                asset.active = False

        # Activate theme-specific CSS and update icons
        if name == 'two':  # Green theme
            self.env.ref(theme_refs['green_css']).active = True
            self.env.ref(theme_refs['green_login']).active = True
            self._update_menu_icons('custom', 'icons_green')
        elif name == 'three':  # Black theme
            self.env.ref(theme_refs['black_css']).active = True
            self.env.ref(theme_refs['black_login']).active = True
            self._update_menu_icons('custom', 'icons')
        else:  # Default theme - restore original Odoo icons
            self._restore_default_icons()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _restore_default_icons(self):
        """Restore default Odoo module icons"""
        # Mapping of menu names to their module names and icon paths
        menu_icon_config = {
            'Contacts': {'module': 'contacts', 'paths': ['contacts/static/description/icon.png']},
            'Link Tracker': {'module': 'link_tracker', 'paths': ['utm/static/description/icon.png']},
            'Dashboards': {'module': 'board', 'paths': ['board/static/description/icon.png']},
            'Sales': {'module': 'sale', 'paths': ['sale/static/description/icon.png']},
            'Invoicing': {'module': 'account', 'paths': ['account/static/description/icon.png']},
            'Accounting': {'module': 'account', 'paths': ['account/static/description/icon.png']},
            'Inventory': {'module': 'stock', 'paths': ['stock/static/description/icon.png']},
            'Purchase': {'module': 'purchase', 'paths': ['purchase/static/description/icon.png']},
            'Calendar': {'module': 'calendar', 'paths': ['calendar/static/description/icon.png']},
            'CRM': {'module': 'crm', 'paths': ['crm/static/description/icon.png']},
            'Note': {'module': 'note', 'paths': ['note/static/description/icon.png']},
            'Website': {'module': 'website', 'paths': ['website/static/description/icon.png']},
            'Point of Sale': {'module': 'point_of_sale', 'paths': ['point_of_sale/static/description/icon.png']},
            'Manufacturing': {'module': 'mrp', 'paths': ['mrp/static/description/icon.png']},
            'Repairs': {'module': 'repair', 'paths': ['repair/static/description/icon.png']},
            'Email Marketing': {'module': 'mass_mailing', 'paths': ['mass_mailing/static/description/icon.png']},
            'SMS Marketing': {'module': 'mass_mailing_sms', 'paths': ['mass_mailing_sms/static/description/icon.png']},
            'Project': {'module': 'project', 'paths': ['project/static/description/icon.png']},
            'Surveys': {'module': 'survey', 'paths': ['survey/static/description/icon.png']},
            'Employees': {'module': 'hr', 'paths': ['hr/static/description/icon.png']},
            'Recruitment': {'module': 'hr_recruitment', 'paths': ['hr_recruitment/static/description/icon.png']},
            'Attendances': {'module': 'hr_attendance', 'paths': ['hr_attendance/static/description/icon.png']},
            'Time Off': {'module': 'hr_holidays', 'paths': ['hr_holidays/static/description/icon.png']},
            'Expenses': {'module': 'hr_expense', 'paths': ['hr_expense/static/description/icon.png']},
            'Maintenance': {'module': 'maintenance', 'paths': ['maintenance/static/description/icon.png']},
            'Live Chat': {'module': 'im_livechat', 'paths': ['im_livechat/static/description/icon.png']},
            'Lunch': {'module': 'lunch', 'paths': ['lunch/static/description/icon.png']},
            'Fleet': {'module': 'fleet', 'paths': ['fleet/static/description/icon.png']},
            'Timesheets': {'module': 'hr_timesheet', 'paths': ['hr_timesheet/static/description/icon.png']},
            'Events': {'module': 'event', 'paths': ['event/static/description/icon.png']},
            'eLearning': {'module': 'website_slides', 'paths': ['website_slides/static/description/icon.png']},
            'Members': {'module': 'membership', 'paths': ['membership/static/description/icon.png']},
            'Apps': {'module': 'base', 'paths': ['base/static/description/modules.png']},
            'Discuss': {'module': 'mail', 'paths': ['mail/static/description/icon.png']},
            'Settings': {'module': 'base', 'paths': ['base/static/description/settings.png']},
        }

        menu_items = self.env['ir.ui.menu'].sudo().search([('parent_id', '=', False)])

        for menu in menu_items:
            icon_config = menu_icon_config.get(menu.name)
            print(menu.name, "===> ", icon_config)
            if icon_config:
                try:
                    icon_found = False
                    for path in icon_config['paths']:
                        try:
                            img_path = odoo.tools.misc.file_path(path)
                            if img_path:
                                with open(img_path, "rb") as img_file:
                                    menu.write({'web_icon_data': base64.b64encode(img_file.read())})
                                _logger.info(f"Restored default icon for menu: {menu.name} from {path}")
                                icon_found = True
                                break
                        except (FileNotFoundError, Exception):
                            continue

                    if not icon_found:
                        _logger.warning(f"Default icon not found for menu '{menu.name}' in module '{icon_config['module']}'")
                except Exception as e:
                    _logger.error(f"Error restoring icon for menu '{menu.name}': {e}")

    def _update_menu_icons(self, source_type='custom', icon_folder=None):
        """Update menu icons based on theme

        Args:
            source_type: 'custom' for custom theme icons, 'default' for Odoo module icons
            icon_folder: folder name for custom icons (e.g., 'icons_black', 'icons_green')
        """
        if source_type == 'default':
            self._restore_default_icons()
            return

        menu_icons = {
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

        menu_items = self.env['ir.ui.menu'].sudo().search([('parent_id', '=', False)])

        for menu in menu_items:
            icon_file = menu_icons.get(menu.name)
            if icon_file:
                try:
                    img_path = odoo.tools.misc.file_path(
                        f'vista_backend_theme/static/src/img/{icon_folder}/{icon_file}')

                    if img_path:
                        with open(img_path, "rb") as img_file:
                            menu.write({'web_icon_data': base64.b64encode(img_file.read())})
                        _logger.info(f"Updated icon for menu: {menu.name}")
                    else:
                        _logger.warning(f"Icon file not found for menu '{menu.name}': {icon_file}")
                except Exception as e:
                    _logger.error(f"Error updating icon for menu '{menu.name}': {e}")

    # Keep the old methods for backward compatibility if needed
    def icon_change_theme_default(self):
        """Legacy method - restores default Odoo icons"""
        self._restore_default_icons()

    def icon_change_theme_green(self):
        """Legacy method - redirects to new implementation"""
        self._update_menu_icons('custom', 'icons_green')

    def icon_change_theme_black(self):
        """Legacy method - redirects to new implementation"""
        self._update_menu_icons('custom', 'icons')


class ThemeStored(models.Model):
    """Store the current theme selection"""
    _name = "theme.data.stored"
    _description = "Stored Theme Data"

    name = fields.Selection([
        ('default', 'Default'),
        ('two', 'Green'),
        ('three', 'Black'),
    ], 'Theme', default='default', required=True)
