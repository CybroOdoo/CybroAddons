# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
    'version': "16.0.1.0.0",
    'summary': """ Multiple Branch Operation Setup for Odoo POS""",
    'description': """ Manages Multiple Branch Operation setup for Odoo Point of 
                    sale.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'category': 'Point of sale',
    'depends': ['base', 'multi_branch_base', 'point_of_sale'],
    'data': [
        'security/multi_branch_pos_security.xml',
        'views/pos_config_views.xml',
        'views/pos_orders_views.xml',
        'views/pos_session_views.xml',
        'report/pos_order_report_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'point_of_sale.assets': [
            'multi_branch_pos/static/src/xml/branch.xml',
        ],
    },
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
