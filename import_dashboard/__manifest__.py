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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Import Dashboard",
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "Centralized dashboard to import data into Odoo using CSV and Excel files with an easy and "
               "organized interface.",
    'description': """The Import Dashboard provides a centralized and user-friendly
                    interface to manage data imports across multiple Odoo modules. It allows users
                    to efficiently import records such as Sales, Purchases, Journal Entries, Products,
                    Partners, Tasks, and more using CSV or Excel files.
                    
                    With structured file handling, dynamic validations, and automated record
                    creation, the dashboard simplifies the import process while reducing errors.
                    It enhances productivity by enabling quick data uploads, clear feedback
                    messages, and seamless integration with existing Odoo workflows, making it
                    ideal for businesses handling large volumes of data.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/import_dashboard_menus.xml',
        'wizard/import_bill_of_material_views.xml',
        'wizard/import_task_views.xml',
        'wizard/import_vendor_pricelist_views.xml',
        'wizard/import_product_template_views.xml',
        'wizard/import_payment_views.xml',
        'wizard/import_attendance_views.xml',
        'wizard/import_product_pricelist_views.xml',
        'wizard/import_partner_views.xml',
        'wizard/import_pos_order_views.xml',
        'wizard/import_journal_entry_views.xml',
        'wizard/import_purchase_order_views.xml',
        'wizard/import_sale_order_views.xml',
        'wizard/import_message_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'import_dashboard/static/src/js/import_dashboard.js',
            'import_dashboard/static/src/xml/dashboard_templates.xml',
            'import_dashboard/static/src/css/style.scss',
        ]
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': True,
}
