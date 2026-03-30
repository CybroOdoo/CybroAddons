# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Theme Kids Care',
    'version': '18.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': "Theme Kids Care is a kids-focused eCommerce "
               "website theme for Odoo 18 with custom snippets and enhanced product layouts.",
    'description': "Theme Kids Care is a responsive eCommerce theme for Odoo 18 "
                   "designed for kids and toy-related online stores. "
                   "It includes custom website snippets, improved shop layouts, "
                   "and Owl Carousel integration for a smoother user experience.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog', 'website_sale', 'website_sale_stock_renting'],
    'data': [
        'views/cart_view.xml',
        'views/contact_us.xml',
        'views/product_view.xml',
        "views/footer.xml",
        "views/variant_templates.xml",
        # Snippets
        "views/snippets/product_offer_snippet.xml",
        "views/snippets/product_testimonials_snippet.xml",
        "views/snippets/toy_feature_right_snippet.xml",
        "views/snippets/toy_feature_left_snippet.xml",
        "views/snippets/product_spotlight_snippet.xml",
        "views/snippets/product_info_showcase_snippet.xml",
        "views/snippets/product_partners_snippet.xml",
        "views/snippets/blog_slider_snippet.xml",
        "views/snippets/all_product_snippet.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            "theme_kids_care/static/src/css/owl_carousel_min.css",
            "theme_kids_care/static/src/css/owl_theme_default_min.css",
            "theme_kids_care/static/src/css/style.css",
            "theme_kids_care/static/src/css/style.scss",
            "theme_kids_care/static/src/js/owl_carousel.js",
            "theme_kids_care/static/src/js/app.js",
        ],
    },
    'images': ['static/description/banner.jpg',
               'static/description/theme_screenshot.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
