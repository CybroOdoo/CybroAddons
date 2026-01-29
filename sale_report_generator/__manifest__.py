# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################

{
    'name': 'Sales All In One Report Generator',
    'version': '15.0.1.0.0',
    'summary': "Dynamic Sales Report Maker",
    'description': "Dynamic Sales Report Maker",
    'category': 'Sale',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_report.xml',
        'report/sale_order_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'sale_report_generator/static/src/js/sale_report.js',
            'sale_report_generator/static/src/css/sale_report.css'
        ],
        'web.assets_qweb': [
            'sale_report_generator/static/src/xml/sale_report_view.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'auto_install': False,
}
