# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Special Product Website Snippet',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': "Select Product and Multiple Template for Product in "
               "Website Snippet",
    'description': "This module gives an option to user to select product "
                   "and multiple template for product in website snippet.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'depends': ['sale_management', 'website', 'base', 'stock', 'website_sale'],
    'data': [
        'views/special_product_snippet_templates.xml',
        'views/product_snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'special_product_snippet/static/src/css/product_snippet.css',
        ],
        'website.assets_wysiwyg': [
            '/special_product_snippet/static/src/js/options.js'
        ],
        'web.assets_backend': [
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
