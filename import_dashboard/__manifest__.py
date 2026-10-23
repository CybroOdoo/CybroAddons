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
    'name': "Import Dashboard",
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Import sale orders, purchase orders, invoices, payments, POS orders, products, partners, pricelists, bills of materials, tasks and attendances from CSV or Excel files.""",
    'description': """ The Import Dashboard feature in Odoo is a powerful tool
     that can save users a significant amount of time when importing large 
     amounts of data into the system. It streamlines the import process and 
     reduces the likelihood of errors, making it a valuable feature for 
     businesses that rely on accurate and timely data.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'base'],
    'data': [
        'security/ir.access.csv',
        'views/res_config_settings_views.xml',
        'views/import_dashboard_menus.xml',
        'wizard/import_message_views.xml',
        'wizard/import_bill_of_material_views.xml',
        'wizard/import_task_views.xml',
        'wizard/import_vendor_pricelist_views.xml',
        'wizard/import_product_template_views.xml',
        'wizard/import_payment_views.xml',
        'wizard/import_attendance_views.xml',
        'wizard/import_product_pricelist_views.xml',
        'wizard/import_partner_views.xml',
        'wizard/import_pos_order_views.xml',
        'wizard/import_invoice_views.xml',
        'wizard/import_purchase_order_views.xml',
        'wizard/import_sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'import_dashboard/static/src/js/import_dashboard.js',
            'import_dashboard/static/src/css/style.scss',
            'import_dashboard/static/src/xml/dashboard_templates.xml',
        ]
    },
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
