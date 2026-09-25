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
from odoo.tools import misc
from odoo.tools.binary import BinaryBytes

MENU_ICONS = {
    "contacts.menu_contacts": "Contacts.png",
    "link_tracker.menu_link_tracker": "Link Tracker.png",
    "spreadsheet_dashboard.menu_root": "Dashboards.png",
    "sale.menu_sale_root": "Sales.png",
    "account.menu_finance": "Invoicing.png",
    "stock.menu_stock_root": "Inventory.png",
    "purchase.menu_purchase_root": "Purchase.png",
    "calendar.mail_menu_calendar": "Calendar.png",
    "crm.crm_menu_root": "CRM.png",
    "project.menu_main_pm": "Project.png",
    "website.menu_website": "Website.png",
    "point_of_sale.menu_point_root": "Point of Sale.png",
    "mrp.menu_mrp_root": "Manufacturing.png",
    "repair.menu_repair_order": "Repairs.png",
    "mass_mailing.mass_mailing_menu_root": "Email Marketing.png",
    "sms.sms_menu_root": "SMS Marketing.png",
    "survey.menu_surveys": "Surveys.png",
    "hr.menu_hr_root": "Employees.png",
    "hr_recruitment.menu_hr_recruitment_root": "Recruitment.png",
    "hr_attendance.menu_hr_attendance_root": "Attendances.png",
    "hr_holidays.menu_hr_holidays_root": "Time Off.png",
    "hr_expense.menu_hr_expense_root": "Expenses.png",
    "maintenance.menu_maintenance_title": "Maintenance.png",
    "im_livechat.menu_livechat_root": "Live Chat.png",
    "lunch.menu_lunch": "Lunch.png",
    "fleet.menu_root": "Fleet.png",
    "hr_timesheet.menu_timesheet_root": "Timesheets.png",
    "event.menu_events": "Events.png",
    "website_slides.menu_website_slides": "eLearning.png",
    "membership.menu_membership_management": "Members.png",
}

def _set_menu_icons(env):
    for xmlid, icon_name in MENU_ICONS.items():
        menu = env.ref(xmlid, raise_if_not_found=False)
        if not menu or menu.parent_id:
            continue
        img_path = misc.file_path(
            "code_backend_theme/static/src/img/icons/%s" % icon_name
        )
        if not img_path:
            continue
        with open(img_path, "rb") as icon_file:
            menu.write({
                "web_icon_data": BinaryBytes(
                    icon_file.read(),
                    filename=icon_name,
                )
            })

def test_pre_init_hook(env):
    _set_menu_icons(env)

def test_post_init_hook(env):
    _set_menu_icons(env)
