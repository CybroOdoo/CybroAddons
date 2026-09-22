# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': "Select Product and Multiple Template for Product in "
               "Website Snippet",
    'description': "This module gives an option to user to select product "
                   "and multiple template for product in website snippet.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'website', 'base', 'stock', 'website_sale'],
    'data': [
        'views/special_product_snippet_templates.xml',
        'views/product_snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'special_product_snippet/static/src/css/product_snippet.css',
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/js/special_product_interaction.js',
        ],
        'website.assets_inside_builder_iframe': [
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/js/special_product_interaction.js',
        ],
        'website.website_builder_assets': [
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/website_builder/special_product_option.xml',
            'special_product_snippet/static/src/website_builder/special_product_plugin.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
