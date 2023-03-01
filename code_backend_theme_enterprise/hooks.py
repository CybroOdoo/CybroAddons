# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


def test_pre_init_hook(cr):
    """Hooks for Changing Menu Web_icon"""

    env = api.Environment(cr, SUPERUSER_ID, {})
    menu_item = env['ir.ui.menu'].search([('parent_id', '=', False)])

    for menu in menu_item:
        if menu.name == 'Contacts':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'contacts.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Link Tracker':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'link.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Dashboards':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'dashboard.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Sales':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'sales.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Accounting':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'accounting.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Inventory':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'inventory.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Purchase':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'purchase.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Calendar':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'calendar.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'CRM':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'crm.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Note':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'notes.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Website':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'website.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Point of Sale':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'pos.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Manufacturing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'manufacturing.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Repairs':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'repair.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Email Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'email-marketing.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'SMS Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'sms.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Project':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'project.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Surveys':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'survey.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Employees':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'employee.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Recruitment':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'recruitment.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Attendances':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'attendance.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Time Off':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'time-off.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Expenses':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'expense.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Maintenance':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'maintenance.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Live Chat':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'chat.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Lunch':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'restaurant.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Fleet':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'traffic.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Timesheets':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'timesheet.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Events':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'token.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'eLearning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'elearning.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Members':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'user.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})

        if menu.name == 'Subscriptions':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'subscription.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Documents':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'documents.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Rental':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'rental.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Marketing Automation':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'marketing_automation.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'IoT':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'iot.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Helpdesk':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'help.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Planning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'planning.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Appraisal':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'appraisal.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Consolidation':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'consolidation.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Payroll':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'payroll.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Barcode':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'barcode.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Quality':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'quality.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'PLM':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'plm.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Field Service':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'field-service.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Data Cleaning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'clean-code.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Approvals':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'approvals.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Referrals':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'referrals.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Discuss':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'discuss.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Social Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'like.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})


def test_post_init_hook(cr, registry):
    """post init hook"""

    env = api.Environment(cr, SUPERUSER_ID, {})
    menu_item = env['ir.ui.menu'].search([('parent_id', '=', False)])

    for menu in menu_item:
        if menu.name == 'Contacts':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'contacts.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Link Tracker':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'link.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Dashboards':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'dashboard.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Sales':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'sales.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Accounting':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'accounting.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Inventory':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'inventory.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Purchase':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'purchase.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Calendar':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'calendar.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'CRM':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'crm.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Note':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'notes.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Website':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'website.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Point of Sale':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'pos.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Manufacturing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'manufacturing.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Repairs':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'repair.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Email Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'email-marketing.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'SMS Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'sms.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Project':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'project.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Surveys':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'survey.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Employees':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'employee.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Recruitment':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'recruitment.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Attendances':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'attendance.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Time Off':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'time-off.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Expenses':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'expense.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Maintenance':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'maintenance.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Live Chat':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'chat.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Lunch':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'restuarant.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Fleet':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'traffic.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Timesheets':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'timesheet.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Events':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'token.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'eLearning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'elearning.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Members':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'user.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})

        if menu.name == 'Subscriptions':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'subscription.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Documents':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'documents.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Rental':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'rental.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Marketing Automation':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'marketing_automation.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'IoT':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'iot.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Helpdesk':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'help.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Planning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'planning.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Appraisal':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'appraisal.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Consolidation':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'consolidation.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Payroll':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'payroll.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Barcode':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'barcode.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Quality':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'quality.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'PLM':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'plm.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Field Service':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'field-service.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Data Cleaning':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'clean-code.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Approvals':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'approvals.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Referrals':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'referrals.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Discuss':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'discuss.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})
        if menu.name == 'Social Marketing':
            img_path = get_module_resource(
                'code_backend_theme_enterprise', 'static', 'src', 'img', 'icons', 'like.png')
            menu.write({'web_icon_data': base64.b64encode(open(img_path, "rb").read())})

