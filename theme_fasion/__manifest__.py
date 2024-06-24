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
    'name': 'Theme Fashion',
    "version": "17.0.1.0.0",
    'category': 'Theme/eCommerce',
    'summary': 'Design Web Pages with Theme Fashion.',
    'description': 'Theme Fashion is a attractive and unique front-end theme'
                   ' mainly suitable for eCommerce website',
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    'depends': ['website_sale','website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/theme_fasion_wizard_views.xml',
        'views/layout_templates.xml',
        'views/header_templates.xml',
        'views/footer_templates.xml',
        'views/blog_templates.xml',
        'views/contact_us_templates.xml',
        'views/products_templates.xml',
        'views/snippets/s_service_templates.xml',
        'views/snippets/s_category_templates.xml',
        'views/snippets/s_smart_clothing_templates.xml',
        'views/snippets/s_insta_shopping_templates.xml',
        'views/snippets/s_banner_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_fasion/static/src/css/animate.min.css',
            'theme_fasion/static/src/css/easyzoom.css',
            'theme_fasion/static/src/css/owl.carousel.min.css',
            'theme_fasion/static/src/css/owl.theme.default.min.css',
            'theme_fasion/static/src/css/pygments.css',
            'theme_fasion/static/src/css/style.css',
            'theme_fasion/static/src/css/custom.css',
            'theme_fasion/static/src/js/owl.carousel.js',
            'theme_fasion/static/src/js/owl.carousel.min.js',
            'theme_fasion/static/src/js/categories_snippet.js',
            'theme_fasion/static/src/js/smart_clothing_snippet.js',
            'theme_fasion/static/src/js/insta_shopping_snippet.js',
            'theme_fasion/static/src/js/custom.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.jpg',
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
