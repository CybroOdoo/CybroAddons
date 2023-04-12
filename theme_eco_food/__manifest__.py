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
    'name': 'Theme Eco Food',
    'description': 'Theme Eco Food is an attractive and modern eCommerce Website theme',
    'summary': 'Design Web Pages with theme EcoLife',
    'category': 'Theme/eCommerce',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale_wishlist', 'website_blog'],
    'data': [
        'data/snippet_products.xml',
        'data/recently_added.xml',
        'data/featured_product_snippet.xml',
        'data/new_arrival.xml',
        'security/ir.model.access.csv',
        'views/shop.xml',
        'views/best_seller.xml',
        'views/recently_added.xml',
        'views/featured_product.xml',
        'views/new_arrival.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/contact.xml',
        'views/cart.xml',
        'views/cart_total_order.xml',
        'views/product_details.xml',
        'views/checkout.xml',
        'views/snippets/banner.xml',
        'views/snippets/client.xml',
        'views/snippets/featured_products.xml',
        'views/snippets/new_arrivals_products.xml',
        'views/snippets/recently_added_products.xml',
        'views/snippets/service.xml',
        'views/snippets/testimoinial.xml',
        'views/snippets/website_ad.xml',
        'views/snippets/ad.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_eco_food/static/src/css/animate.css',
            'theme_eco_food/static/src/xml/snippets/best_seller.xml',
            'theme_eco_food/static/src/xml/snippets/featured_products.xml',
            'theme_eco_food/static/src/xml/snippets/new_arrival_products.xml',
            'theme_eco_food/static/src/xml/snippets/recently_added.xml',
            'theme_eco_food/static/src/css/animate.min.css',
            'theme_eco_food/static/src/css/bootstrap-dropdownhover.css',
            'theme_eco_food/static/src/css/bootstrap-dropdownhover.min.css',
            'theme_eco_food/static/src/css/bootstrap-icons.css',
            'theme_eco_food/static/src/css/owl.carousel.min.css',
            'theme_eco_food/static/src/css/owl.theme.default.min.css',
            'theme_eco_food/static/src/css/shuffle-styles.css',
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css',
            'theme_eco_food/static/src/css/style.css',
            'https://code.jquery.com/jquery-1.12.4.js',
            'https://code.jquery.com/ui/1.12.1/jquery-ui.js',
            'theme_eco_food/static/src/js/owl.carousel.js',
            'theme_eco_food/static/src/js/owl.carousel.min.js',
            'theme_eco_food/static/src/js/script.js',
            'theme_eco_food/static/src/js/index.js',
            'theme_eco_food/static/src/js/new_arrivals.js',
            'theme_eco_food/static/src/js/best_seller.js',
            'theme_eco_food/static/src/js/featured_products.js',
            'theme_eco_food/static/src/js/recently_added.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/js/bootstrap.bundle.min.js',

        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
