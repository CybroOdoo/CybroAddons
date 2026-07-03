# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Open HRMS Disciplinary Tracking',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Employee Disciplinary Tracking Management""",
    'description': """The primary goal of disciplinary tracking is to ensure 
     that employees adhere to company policies and regulations, and when 
     violations occur, to address them appropriately.""",
    'live_test_url': 'https://youtu.be/LFuw2iY4Deg',
    'author': 'Cybrosys Techno Solutions, Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/disciplinary_action_security.xml',
        'data/ir_sequence_data.xml',
        'views/disciplinary_action_views.xml',
        'views/discipline_category_views.xml',
    ],
    'demo': [
        'data/hr_department_demo.xml',
        'data/hr_work_location_demo.xml',
        'data/hr_employee_demo.xml',
        'data/discipline_category_demo.xml',
        'data/disciplinary_action_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
