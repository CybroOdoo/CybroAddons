# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': "Monday.com Odoo Connector",
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': """Provides opportunity to connect with your Monday.com 
     account from Odoo""",
    'description': """Monday.com Odoo connector module allows to connect with 
     your Monday.com account and import Users, Boards, Groups, Items and 
     Customers from Monday.com to Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['contacts'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/monday_connector_views.xml',
        'views/monday_credential_views.xml',
        'views/monday_board_views.xml',
        'views/monday_group_views.xml',
        'views/monday_item_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/item_column_value_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
