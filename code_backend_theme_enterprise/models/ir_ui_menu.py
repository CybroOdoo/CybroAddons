# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aswin A K (odoo@cybrosys.com)
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
from odoo import api, models

ICON_PATH = 'code_backend_theme_enterprise,static/src/img/icons/'

# Root menu name -> icon file name
MENU_ICONS = {
    'Contacts': 'contacts.png',
    'Link Tracker': 'link.png',
    'Dashboards': 'dashboard.png',
    'Sales': 'sales.png',
    'Accounting': 'accounting.png',
    'Invoicing': 'accounting.png',
    'Inventory': 'inventory.png',
    'Purchase': 'purchase.png',
    'Calendar': 'calendar.png',
    'CRM': 'crm.png',
    'Note': 'notes.png',
    'To-do': 'notes.png',
    'Website': 'website.png',
    'Point of Sale': 'pos.png',
    'Manufacturing': 'manufacturing.png',
    'Repairs': 'repair.png',
    'Email Marketing': 'email-marketing.png',
    'SMS Marketing': 'sms.png',
    'Project': 'project.png',
    'Surveys': 'survey.png',
    'Employees': 'employee.png',
    'Recruitment': 'recruitment.png',
    'Attendances': 'attendance.png',
    'Time Off': 'time-off.png',
    'Expenses': 'expense.png',
    'Maintenance': 'maintenance.png',
    'Live Chat': 'chat.png',
    'Lunch': 'restaurant.png',
    'Fleet': 'traffic.png',
    'Timesheets': 'timesheet.png',
    'Events': 'token.png',
    'eLearning': 'elearning.png',
    'Members': 'user.png',
    'Subscriptions': 'subscription.png',
    'Documents': 'documents.png',
    'Rental': 'rental.png',
    'Marketing Automation': 'marketing_automation.png',
    'IoT': 'iot.png',
    'Helpdesk': 'help.png',
    'Planning': 'planning.png',
    'Appraisal': 'appraisal.png',
    'Consolidation': 'consolidation.png',
    'Payroll': 'payroll.png',
    'Barcode': 'barcode.png',
    'Quality': 'quality.png',
    'PLM': 'plm.png',
    'Field Service': 'field-service.png',
    'Data Cleaning': 'clean-code.png',
    'Approvals': 'approvals.png',
    'Referrals': 'referral.png',
    'Discuss': 'discuss.png',
    'Social Marketing': 'like.png',
}


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _cbt_apply_theme_icons(self):
        """Replace the web icon of known root menus with the theme icons.

        Called from data/menu_icons.xml, so it runs on module install AND on
        every module upgrade. Writing ``web_icon`` ("module,path") lets
        ``ir.ui.menu`` load the image itself, as ``<menuitem web_icon>`` does.
        Menus are matched on their English name, whatever the user language.
        """
        root_menus = self.with_context(lang='en_US', active_test=False).search(
            [('parent_id', '=', False)])
        for menu in root_menus:
            icon = MENU_ICONS.get(menu.name)
            if icon and menu.web_icon != ICON_PATH + icon:
                menu.write({'web_icon': ICON_PATH + icon})
