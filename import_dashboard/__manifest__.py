# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Import Dashboard",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module facilitates the import of data from various '
               'modules through a single window',
    'description': """The Import Dashboard feature in Odoo is a powerful tool 
    that can save users a significant amount of time when importing large 
    amounts of data into the system. It streamlines the import process and 
    reduces the likelihood of errors, making it a valuable feature for 
    businesses that rely on accurate and timely data.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/import_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/import_attendance_views.xml',
        'wizard/import_bill_of_material_views.xml',
        'wizard/import_invoice_views.xml',
        'wizard/import_message_views.xml',
        'wizard/import_partner_views.xml',
        'wizard/import_payment_views.xml',
        'wizard/import_pos_views.xml',
        'wizard/import_product_pricelist_views.xml',
        'wizard/import_product_template_views.xml',
        'wizard/import_purchase_order_views.xml',
        'wizard/import_sale_order_views.xml',
        'wizard/import_task_views.xml',
        'wizard/import_vendor_pricelist_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'import_dashboard/static/src/js/import_dashboard.js',
            'import_dashboard/static/src/css/style.scss',
        ],
        'web.assets_qweb': [
            'import_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'external_dependencies': {
        'python': ['xlrd']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
