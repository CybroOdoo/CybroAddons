# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
{
    'name': 'Product Search Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': """Product Search Snippet for Website.""",
    'description': """This module enables users to search for products
    within a specific category or across all categories using the search
    bar on the website snippet and redirect to its details.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'depends': ['website', 'sale_management'],
    'data': ['views/snippets/search_snippet_templates.xml',
             'views/snippets/product_search_templates.xml',
             'views/snippets/product_details_templates.xml',
             'views/snippets/selected_product_from_all_product_templates.xml',
             'views/snippets/product_all_result_templates.xml',
             'views/snippets/category_details_templates.xml',
             'views/snippets/category_selected_product_templates.xml',
             'views/snippets/selected_category_from_all_category_templates.xml',
             'views/snippets/category_all_result_templates.xml',
             'views/snippets/product_select_from_category_templates.xml',
             ],
    'assets': {
        'web.assets_frontend': [
            'website_product_search_snippet/static/src/css/website_product_search_snippet.scss',
            'website_product_search_snippet/static/src/js/website_product_search_snippet.js',
            'website_product_search_snippet/static/src/js/search_bar.js',
            'website_product_search_snippet/static/src/xml/product_templates.xml',
            'website_product_search_snippet/static/src/xml/category_templates.xml',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
