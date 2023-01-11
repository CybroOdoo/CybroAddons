# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
    'name': "Multiple Branch Setup for POS",
    'version': "15.0.1.1.0",
    'summary': """ Multiple Branch Unit Operation Setup for Odoo POS""",
    'description': """ Multiple Branch Unit Operation Setup for  Odoo POS""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'category': 'Tools',
    'depends': ['base', 'multi_branch_base', 'point_of_sale'],
    'data': [
        'security/pos_security.xml',
        'views/branch_pos_config_views.xml',
        'views/branch_pos_orders_views.xml',
        'views/branch_pos_session_views.xml',
        'report/pos_order_report.xml'
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'point_of_sale.assets': [
            'multi_branch_pos/static/src/js/branch.js',
        ],
        'web.assets_qweb': [
            'multi_branch_pos/static/src/xml/branch.xml',
        ],
    },
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
