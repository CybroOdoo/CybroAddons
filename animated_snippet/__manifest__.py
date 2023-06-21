# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ahammed Harshad(<https://www.cybrosys.com>)
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
    'name': "Animated Snippets",
    'version': '16.0.1.0.0',
    'summary': """Animated Snippets for Websites.""",
    'description': """Variety of Snippets With Animations to Beautify your Website.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Website',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'web_editor'],
    'data': [
        'views/snippets/snippets.xml',
        'views/snippets/a_features_01_templates.xml',
        'views/snippets/a_columns_templates.xml',
        'views/snippets/a_image_gallery_templates.xml',
        'views/snippets/a_features_02_templates.xml',
        'views/snippets/a_features_03_templates.xml',
        'views/snippets/a_features_04_templates.xml',
        'views/snippets/a_color_blocks_templates.xml',
        'views/snippets/a_features_05_templates.xml',
        'views/snippets/a_features_06_templates.xml',
        'views/snippets/a_features_07_templates.xml',
        'views/snippets/a_features_templates.xml',
        'views/snippets/a_showcase_templates.xml',
        'views/snippets/a_features_08_templates.xml',
        'views/snippets/a_features_09_templates.xml',
        'views/snippets/a_numbers_templates.xml',
        'views/snippets/a_product_list_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/animated_snippet/static/src/css/a_features.css',
            '/animated_snippet/static/src/css/a_color_blocks.css',
            '/animated_snippet/static/src/css/a_columns.css',
            '/animated_snippet/static/src/css/a_features_01.css',
            '/animated_snippet/static/src/css/a_features_02.css',
            '/animated_snippet/static/src/css/a_features_03.css',
            '/animated_snippet/static/src/css/a_features_04.css',
            '/animated_snippet/static/src/css/a_features_05.css',
            '/animated_snippet/static/src/css/a_features_06.css',
            '/animated_snippet/static/src/css/a_features_07.css',
            '/animated_snippet/static/src/css/a_features_08.css',
            '/animated_snippet/static/src/css/a_features_09.css',
            '/animated_snippet/static/src/css/a_image_gallery.css',
            '/animated_snippet/static/src/css/a_numbers.css',
            '/animated_snippet/static/src/css/a_product_list.css',
            '/animated_snippet/static/src/css/a_showcase.css',
        ]},
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
