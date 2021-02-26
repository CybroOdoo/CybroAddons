# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    'name': 'Point of Sale Logo',
    'version': '14.0.1.0.0',
    'summary': """Logo For Every Point of Sale (Screen & Receipt)""",
    'description': """"This module helps you to set a logo for every point of sale. This will help you to
                 identify the point of sale easily. You can also see this logo in pos screen and pos receipt.""",
    'category': 'Point Of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_config_image_view.xml',
        'views/pos_image_view.xml',
    ],
    'qweb': ['static/src/xml/pos_ticket_view.xml',
             'static/src/xml/pos_screen_image_view.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
