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
    'name': 'Advanced POS Reports',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Generates various reports from POS screen and reporting menu""",
    'description': """Generates various reports like, top 
     selling products / categories / customers report, ongoing sessions report 
     under reporting menu.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'stock'],
    'data': [
        'security/ir.access.csv',
        'wizard/pos_sale_ongoing_views.xml',
        'wizard/pos_sale_top_selling_views.xml',
        'wizard/advanced_pos_reports_wizard.xml',
        'report/advanced_pos_reports.xml',
        'report/pos_ongoing_session_templates.xml',
        'report/pos_top_selling_categories_templates.xml',
        'report/pos_top_selling_customers_templates.xml',
        'report/pos_top_selling_products_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'advanced_pos_reports/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
