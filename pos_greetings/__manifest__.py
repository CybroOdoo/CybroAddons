# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: YADHU K (odoo@cybrosys.com)
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
    'name': 'POS Customer Greeting Messages',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Send Greeting messages to Customers in Pos Order',
    'description': 'Send Greeting messages to Customers in Pos Order',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'external_dependencies': {'python': ['twilio']},
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_settings.xml',
        'views/pos_greetings_view.xml',
    ],
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,

}
