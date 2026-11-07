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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Sale Report Format Editor',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sale Report Format Editor For Configuring the Sale Report '
               'Templates',
    'description': 'In the Sale Format Editor App, We can configure the sale '
                   'fields to our own need.There we can have 4 types of '
                   'templates - Default, Normal, Modern, Old Standard. '
                   'We can also customize and hide the fields',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
             'security/ir.access.csv',
             'data/doc_layout_data.xml',
             'report/report_sale_templates.xml',
             'report/sale_normal_templates.xml',
             'report/sale_modern_templates.xml',
             'report/sale_old_templates.xml',
             'report/preview_layout_report_templates.xml',
             'views/doc_layout_views.xml',
             'views/custom_external_layout_templates.xml',
             'wizard/base_document_layout_views.xml',
             'views/default_preview_templates.xml',
             'views/normal_preview_templates.xml',
             'views/modern_preview_templates.xml',
             'views/old_preview_templates.xml',
             ],
    'images': [
        'static/description/banner.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
