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
"""Hooks for Changing Menu Web_icon"""
import base64

from odoo.modules import get_module_resource

MENU_ICON_MAP = {
    # Top-level menus whose icons are overwritten by this theme at install time.
    "Contacts": "contact.png",
    "Link Tracker": "link-tracker.png",
    "Dashboards": "dashboard.png",
    "Sales": "sales.png",
    "Invoicing": "invoice.png",
    "Inventory": "inventory.png",
    "Purchase": "purchase.png",
    "Calendar": "calendar.png",
    "CRM": "crm.png",
    "Notes": "notes.png",
    "Website": "website.png",
    "Point of Sale": "pos.png",
    "Manufacturing": "manufacturing.png",
    "Repairs": "repairs.png",
    "Email Marketing": "marketing.png",
    "SMS Marketing": "sms-marketing.png",
    "Project": "project.png",
    "Surveys": "surveys.png",
    "Employees": "employees.png",
    "Recruitment": "recruitment.png",
    "Attendances": "attendance.png",
    "Time Off": "time-off.png",
    "Expenses": "expense.png",
    "Maintenance": "maintenance.png",
    "Live Chat": "live-chat.png",
    "Lunch": "lunch.png",
    "Fleet": "fleet.png",
    "Timesheets": "timesheets.png",
    "Events": "events.png",
    "eLearning": "elearning.png",
    "Members": "members.png",
}


def _theme_icon_b64(icon_filename):
    img_path = get_module_resource(
        "backend_theme_infinito", "static", "src", "img", "icons", icon_filename
    )
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read())


def icons_post_init_hook(env):
    """Post init hook for changing menu icons and resetting dynamic CSS.

    Note: This writes on existing `ir.ui.menu` records, so it must also be
    reverted on uninstall to avoid leaving permanent UI changes behind.
    Clears any stale dynamic_css parameter (e.g. migrated from Odoo 17) so
    the theme starts with a clean stylesheet on every fresh install.
    Also removes the old Odoo 17 ir.asset record that bundled the physical
    dynamic_styles.css static file, which pollutes the asset bundle when the
    database was migrated or the Odoo 17 module path is still on the addons path.
    """
    set_param = env['ir.config_parameter'].sudo().set_param

    set_param('backend_theme_infinito.dynamic_css', '')

    # Enable sidebar by default so the theme's navigation is visible on fresh installs.
    set_param('backend_theme_infinito.is_sidebar_enabled', 'True')
    set_param('backend_theme_infinito.is_sidebar_icon', 'True')
    set_param('backend_theme_infinito.is_sidebar_name', 'True')
    set_param('backend_theme_infinito.is_sidebar_company', 'True')
    set_param('backend_theme_infinito.is_sidebar_user', 'True')

    # Remove stale ir.asset record left by the Odoo 16/17 version of this theme.
    # That version registered dynamic_styles.css as a bundle file; Odoo 18 serves
    # it via a controller instead, so the record must not exist.
    stale_asset = env['ir.asset'].sudo().search([
        ('path', 'like', 'backend_theme_infinito/static/src/css/dynamic_styles.css')
    ])
    if stale_asset:
        stale_asset.unlink()

    menus = env["ir.ui.menu"].sudo().search([("parent_id", "=", False)])
    for menu in menus:
        filename = MENU_ICON_MAP.get(menu.name)
        if not filename:
            continue
        menu.write({"web_icon_data": _theme_icon_b64(filename)})


def icons_uninstall_hook(env):
    """Uninstall hook to restore default icons.

    Uninstalling a module does not rollback writes done on existing records.
    This hook restores menu icons to their defaults if they were set by this theme.
    """
    Menu = env["ir.ui.menu"].sudo()

    # Restore the `web_icon` overrides done by `views/icons.xml` first.
    # In Odoo 18, the app grid uses `web_icon_data` attachments returned by
    # `ir.ui.menu.load_menus()`. Restoring `web_icon` will also recompute and
    # store `web_icon_data` via the core `write()` override.
    def _restore_web_icon(xmlid, theme_value, default_value):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and rec.web_icon == theme_value:
            rec.write({"web_icon": default_value})

    _restore_web_icon(
        "base.menu_administration",
        "backend_theme_infinito,static/src/img/icons/settings.png",
        "base,static/description/settings.png",
    )
    _restore_web_icon(
        "base.menu_management",
        "backend_theme_infinito,static/src/img/icons/apps.png",
        "base,static/description/modules.png",
    )
    _restore_web_icon(
        "mail.menu_root_discuss",
        "backend_theme_infinito,static/src/img/icons/discuss.png",
        "mail,static/description/icon.png",
    )

    # Restore menus that were overwritten via `web_icon_data` only if the stored
    # data matches the theme's icon (avoid clobbering user customizations).
    menus = Menu.search([("parent_id", "=", False)])
    for menu in menus:
        filename = MENU_ICON_MAP.get(menu.name)
        if not filename:
            continue
        try:
            if menu.web_icon_data and menu.web_icon_data == _theme_icon_b64(filename):
                # Recompute the default icon data from the menu's `web_icon`.
                # Clearing `web_icon_data` would result in the fallback cube icon.
                menu.write({"web_icon": menu.web_icon})
        except Exception:
            # Best-effort restore: still try to recompute from `web_icon` so we don't
            # leave the menu with a missing icon.
            menu.write({"web_icon": menu.web_icon})
