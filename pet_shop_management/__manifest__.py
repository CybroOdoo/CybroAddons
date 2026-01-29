# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
    'name': 'Pet Shop Management',
    'version': '15.0.1.0.0',
    'category': 'Sales',
    'summary': 'Pet shop management module is used mange the pet selling and sitting',
    'description': """Pet shop management module is used to mange the pets , 
    their selling sitting and their sitting can be scheduled with the sitting 
    employees, and can be see the pets sitting schedule and pet information through 
    the website also.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'hr', 'stock', 'website'],
    'data': [
        'security/pet_shop_management_groups.xml',
        'security/hr_employee_security.xml',
        'security/product_product_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/sitting_schedule_views.xml',
        'views/pet_type_views.xml',
        'views/product_product_views.xml',
        'views/working_time_views.xml',
        'views/pets_portal_templates.xml',
        'views/pet_sittings_templates.xml',
        'views/sale_order_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/pet_shop_management_menu.xml',
        'reports/pet_information_template.xml',
        'reports/pet_shop_management_report.xml',
        'wizards/pet_setting_schedule_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
