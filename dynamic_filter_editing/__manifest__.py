# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'Dynamic Filter Editing',
    'version': "16.0.1.0.0",
    'category': 'Extra Tools',
    'summary': "This app is designed to assist users in editing"
               " custom filters",
    'description': "Through this app, users have the ability to edit custom"
                   "filters effortlessly. They can conveniently add multiple"
                   "filters, remove existing ones, and even make simultaneous"
                   "edits to multiple values, providing a seamless and "
                   "efficient editing experience.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base', 'web',
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_filter_editing/static/src/js/search_bar.js',
            'dynamic_filter_editing/static/src/js/filter.js',
            'dynamic_filter_editing/static/src/xml/web_searchbar_facet_views.xml',
            'dynamic_filter_editing/static/src/xml/custom_filter_dialog_views.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
