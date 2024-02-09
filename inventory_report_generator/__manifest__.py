# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Inventory All In One Report Generator',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': "Dynamic Inventory Report Generator for Odoo 17",
    'description': "Streamline your inventory reporting with ease. Generate "
                   "dynamic reports, gain insights, and make informed "
                   "decisions.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_report_views.xml',
        'report/inventory_pdf_report_templates.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_report_generator/static/src/js/inventory_report.js',
            'inventory_report_generator/static/src/css/inventory_report.css',
            'inventory_report_generator/static/src/xml/inventory_report_templates.xml',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
