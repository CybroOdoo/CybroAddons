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
    'name': 'POS All in One Report Generator',
    'version': '15.0.1.1.1',
    'summary': "Dynamic Point Of Sale Report Maker",
    'description': "Dynamic Point Of Sale Report Maker",
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
                'point_of_sale',
                'stock',
                'web'
                ],
    'data': [
            'security/ir.model.access.csv',
            'report/pos_order_report.xml',
            'views/pos_report.xml',
            ],
    'assets': {
        'web.assets_backend': [
            'pos_report_generator/static/src/js/action_manager.js',
            'pos_report_generator/static/src/js/pos_report.js',
            'pos_report_generator/static/src/css/pos_report.css'
        ],
        'web.assets_qweb': [
            'pos_report_generator/static/src/xml/pos_report_view.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'auto_install': False,
}
