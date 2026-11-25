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
{
    'name': 'Pet Shop Management',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': """This module is used to manage pet sales and sitting.""",


    'description': """This module is used to manage pet sales and sitting
    services. It allows users to schedule pet sittings, which can be viewed and
    managed from the website portal.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'hr', 'stock', 'website'],
    'data': [
        'security/pet_shop_management_groups.xml',
        'security/ir.access.csv',
        'security/pet_shop_management_security.xml',
        'data/ir_sequence_data.xml',
        'data/portal_entry_data.xml',
        'report/pet_information_template.xml',
        'report/report.xml',
        'wizard/pet_setting_schedule_views.xml',
        'views/sitting_schedule_views.xml',
        'views/pet_type_views.xml',
        'views/product_product_views.xml',
        'views/working_shifts.xml',
        'views/pets_portal_templates.xml',
        'views/sittings_portal_templates.xml',
        'views/sale_order_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/pet_shop_management_menu.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
