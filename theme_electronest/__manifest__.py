# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    'name': 'Theme Electronest',
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': 'Design The Web Pages with theme Electronest',
    'description': 'Theme Electronest is a specialized web design module for Odoo, '
                   'providing a range of tools and '
                   'features to streamline the process of designing and '
                   'developing websites within the Odoo platform.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale'],
    'data': [
        "data/ir_ui_view_data.xml",
        "views/contacts_templates.xml",
        "views/header.xml",
        "views/footer.xml",
        "views/website_sale_templates.xml",
        "views/website_cart_views.xml",
        "views/product_view.xml",
        "views/snippets/about_us_snippet.xml",
        "views/snippets/product_offer_banner_snippet.xml",
        "views/snippets/top_categories_snippet.xml",
        "views/snippets/best_offers_snippet.xml",
        "views/snippets/product_showcase_snippet.xml",
        "views/snippets/promotional_banner_slider_snippet.xml",
        "views/about.xml",
        "views/home.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_electronest/static/src/css/style.css',
            'theme_electronest/static/src/js/website_sale.js',
            'theme_electronest/static/src/js/app.js',
            "theme_electronest/static/src/scss/off_canvas.scss",
            "theme_electronest/static/src/scss/animation.scss",
            "https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css",
            "https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
