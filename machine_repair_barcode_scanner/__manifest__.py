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
    'name': "Machine Repair Barcode Scanner",
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Barcode Scanner in Repair Orders',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_machine_repair_management'],
    'data': [
        'views/machine_repair_views.xml',
        'views/product_product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'machine_repair_barcode_scanner/static/src/js/machine_barcode_scan.js',
            'machine_repair_barcode_scanner/static/src/css/styles.css',
            'machine_repair_barcode_scanner/static/src/xml/machine_repair_barcode_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

