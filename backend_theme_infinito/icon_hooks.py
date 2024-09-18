"""Hooks for Changing Menu Web_icon"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, SUPERUSER_ID
from odoo.modules import get_module_resource


def icons_post_init_hook(cr, registry):
    """post init hook for changing module icons"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    menu_item = env['ir.ui.menu'].search([('parent_id', '=', False)])

    icons_dictionary = {
        'Contacts': 'contact.png',
        'Link Tracker': 'link-tracker.png',
        'Dashboards': 'dashboard.png',
        'Sales': 'sales.png',
        'Invoicing': 'invoice.png',
        'Inventory': 'inventory.png',
        'Purchase': 'purchase.png',
        'Calendar': 'calendar.png',
        'CRM': 'crm.png',
        'Notes': 'notes.png',
        'Website': 'website.png',
        'Point of Sale': 'pos.png',
        'Manufacturing': 'manufacturing.png',
        'Repairs': 'repairs.png',
        'Email Marketing': 'marketing.png',
        'SMS Marketing': 'sms-marketing.png',
        'Project': 'project.png',
        'Surveys': 'surveys.png',
        'Employees': 'employees.png',
        'Recruitment': 'recruitment.png',
        'Attendances': 'attendance.png',
        'Time Off': 'time-off.png',
        'Expenses': 'expense.png',
        'Maintenance': 'maintenance.png',
        'Live Chat': 'live-chat.png',
        'Lunch': 'lunch.png',
        'Fleet': 'fleet.png',
        'Timesheets': 'timesheets.png',
        'Events': 'events.png',
        'eLearning': 'elearning.png',
        'Members': 'members.png',
    }

    for menu in menu_item:
        filename = icons_dictionary.get(menu.name)
        if filename:
            img_path = get_module_resource(
                'backend_theme_infinito', 'static', 'src', 'img', 'icons', filename)
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
