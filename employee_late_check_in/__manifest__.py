# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "Employee Late Check-in",
    "version": "16.0.1.0.1",
    "category": "Human Resources",
    "summary": "Employee Late Check-in module for tracking and managing late "
    "check-ins of employees and may deduct salary from payslip",
    "description": "The module is designed for meticulous tracking and "
    "management of employee punctuality. It enables "
    "organizations to monitor late check-ins efficiently, "
    "offering insights into tardiness patterns. With a "
    "user-friendly interface, it provides a comprehensive "
    "overview of individual employee records, facilitating "
    "timely interventions. This module contributes to fostering"
    " a punctual and efficient work environment.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["hr_attendance", "hr_payroll_community"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "data/salary_rule.xml",
        "views/res_config_settings_views.xml",
        "views/hr_attendance_views.xml",
        "views/late_check_in_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_payslip_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init_hook"
}
