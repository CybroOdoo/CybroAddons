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
from odoo.modules import get_resource_from_path

_logger = logging.getLogger(__name__)


def _update_menu_icons(cr, menu_icons):
    """Helper function to update menu icons"""
    menu_item = cr['ir.ui.menu'].search([('parent_id', '=', False)])

    for menu in menu_item:
        icon_file = menu_icons.get(menu.name)
        if icon_file:
            img_path = get_resource_from_path(
                f'vista_backend_theme/static/src/img/icons/{icon_file}')

            if img_path:
                try:
                    with open(img_path, "rb") as img_file:
                        menu.write({'web_icon_data': base64.b64encode(img_file.read())})
                    _logger.info(f"Updated icon for menu: {menu.name}")
                except Exception as e:
                    _logger.warning(f"Failed to update icon for menu '{menu.name}': {e}")
            else:
                _logger.warning(f"Icon file not found for menu '{menu.name}': {icon_file}")


def test_pre_init_hook(cr):
    """pre init hook"""
    menu_icons = {
        'Contacts': 'contacts.png',
        'Link Tracker': 'link-tracker.png',
        'Dashboards': 'dashboards.png',
        'Sales': 'sales.png',
        'Invoicing': 'accounting.png',
        'Inventory': 'inventory.png',
        'Purchase': 'purchase.png',
        'Calendar': 'calendar.png',
        'CRM': 'crm.png',
        'Note': 'notes.png',
        'Notes': 'notes.png',
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
    }

    _update_menu_icons(cr, menu_icons)


def test_post_init_hook(cr):
    """post init hook"""
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
    }

    _update_menu_icons(cr, menu_icons)