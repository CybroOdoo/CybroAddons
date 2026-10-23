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
    'name': 'Dynamic Product Label Print',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': "Print dynamic product labels and barcodes for multiple products",
    'description': "Dynamically print the barcode and product fields of multiple products",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock'],
    'data': [
        'security/ir.access.csv',
        'report/label_layout_templates.xml',
        'views/dynamic_template_views.xml',
        'wizard/product_label_layout_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',

    'installable': True,
    'auto_install': False,
    'application': False,
}
