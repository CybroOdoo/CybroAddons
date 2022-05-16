# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Custom List View',
    'version': '15.0.1.0.0',
    'summary': 'Helps to Show Row Number, Fixed Header, Duplicate Record and Highlight Selected Record in List View',
    'description': 'Helps to Show Row Number, Fixed Header, Duplicate Record and Highlight Selected Record in List View',
    'category': 'Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'depends': ['base'],
    'data': [

    ],
    'assets': {
            'web.assets_backend': [
                'custom_list_view/static/src/js/duplicate_record.js',
                'custom_list_view/static/src/js/serial_no.js',
                'custom_list_view/static/src/js/record_highlight.js',
                'custom_list_view/static/src/css/sticky_header.css',
                'custom_list_view/static/src/css/highlight.css'

            ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
