# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Advanced Search Widget',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "It elevates the design of search menu items and offers" 
               "sophisticated expression options for filtering categories",
    'description': "An Advanced Search Widget could be custom widget designed"
                   "to enhance the search capabilities. It might offer more" 
                   "advanced filtering options and search criteria.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'advanced_search_widget/static/src/js/domain_tree.js',
            'advanced_search_widget/static/src/js/domain_selector_dialog.js',
            'advanced_search_widget/static/src/js/SearchWidget.js',
            'advanced_search_widget/static/src/js/search_bar.js',
            'advanced_search_widget/static/src/js/search_model.js',
            'advanced_search_widget/static/src/xml/custom_favorite_item.xml',
            'advanced_search_widget/static/src/xml/custom_groupby_item.xml',
            'advanced_search_widget/static/src/xml/SearchWidget.xml',
            'advanced_search_widget/static/src/xml/search_bar.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
