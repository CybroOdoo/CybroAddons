# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'POS Product Create Edit',
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Create or edit products directly from the Point'
               ' of Sale interface.',
    'description': 'This module allows users to create or edit products '
                   'directly from the Point of Sale (POS) interface.'
                   ' It provides a convenient way to manage products'
                   ' on the fly without navigating to the backend.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': ['views/assets.xml'],
    'qweb': [
        'static/src/xml/product_button_templates.xml',
        'static/src/xml/product_create_popup_templates.xml',
        'static/src/xml/product_edit_popup_templates.xml',
        'static/src/xml/product_line_templates.xml',
        'static/src/xml/product_list_screen_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
