# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O @cybrosys(odoo@cybrosys.com)
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
    'name': 'Create Products From POS',
    'version': '14.0.1.0.1',
    'category': 'Point of Sale',
    'summary': 'Create Products From POS Interface',
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'depends': ['point_of_sale'],
    'data': [
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/product_create_button.xml',
        'static/src/xml/product_create_popup.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
