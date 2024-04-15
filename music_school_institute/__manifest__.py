# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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
{
    "name": "Music School Institute",
    "version": "17.0.1.0.0",
    "category": "Industries",
    "summary": "Efficiently manage teachers, students, classes, attendance, "
    "fees, and more with our Music School Management module. ",
    "description": """Simplify music school operations with this comprehensive 
    Odoo module. Manage teachers and students, track attendance, handle fees,
    and plan events effortlessly. Stay organized and focus on nurturing 
    musical talent.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["stock", "sale", "calendar", "event", "hr"],
    "data": [
        "security/music_school_institute_groups.xml",
        "security/music_school_institute_security.xml",
        "security/ir.model.access.csv",
        "views/class_type_views.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/hr_employee_views.xml",
        "views/class_lesson_views.xml",
        "views/students_attendance_views.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/banner.jpg"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
