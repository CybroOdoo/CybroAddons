# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas(odoo@cybrosys.com)
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
    'name': "Table Reservation in POS",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """The Table Reservation in Pos module is used to facilitate
    the management of reservations""",
    'description': 'The Table Reservation in Pos module is a comprehensive'
                   ' solution that combines reservation management with the '
                   'functionality of a reserve table in POS system.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'depends': ['base', 'point_of_sale', 'pos_restaurant'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'table_reservation_in_pos/static/src/xml/*',
            'table_reservation_in_pos/static/src/js/*',
            'table_reservation_in_pos/static/src/scss/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
