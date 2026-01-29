# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Eco Food',
    'version': '15.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Design Web Pages with theme EcoLife',
    'description': 'Theme Eco Food is an attractive and modern '
                   'eCommerce Website theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist', 'website_blog',
                'website_sale_comparison'],
    'data': [
        'security/ir.model.access.csv',
        'data/dynamic_product_data.xml',
        'data/recently_added_product_data.xml',
        'data/featured_product_data.xml',
        'data/new_arrival_data.xml',
        'views/products_templates.xml',
        'views/dynamic_product_views.xml',
        'views/recently_added_product_views.xml',
        'views/featured_product_views.xml',
        'views/new_arrival_views.xml',
        'views/layout_templates.xml',
        'views/template_header_default_templates.xml',
        'views/contactus_templates.xml',
        'views/product_templates.xml',
        'views/address_templates.xml',
        'views/snippets/banner_template.xml',
        'views/snippets/best_seller_template.xml',
        'views/snippets/client_template.xml',
        'views/snippets/featured_product_template.xml',
        'views/snippets/new_arrival_template.xml',
        'views/snippets/recently_added_template.xml',
        'views/snippets/service_template.xml',
        'views/snippets/testimonial_template.xml',
        'views/snippets/website_ad_template.xml',
        'views/snippets/ad_template.xml',
        'views/snippets/snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_eco_food/static/src/css/animate.css',
            'theme_eco_food/static/src/css/animate.min.css',
            'theme_eco_food/static/src/css/bootstrap-dropdownhover.css',
            'theme_eco_food/static/src/css/bootstrap-dropdownhover.min.css',
            'theme_eco_food/static/src/css/bootstrap-icons.css',
            'theme_eco_food/static/src/css/owl.carousel.min.css',
            'theme_eco_food/static/src/css/owl.theme.default.min.css',
            'theme_eco_food/static/src/css/shuffle-styles.css',
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/'
            'bootstrap-icons.css',
            'theme_eco_food/static/src/css/style.css',
            'theme_eco_food/static/src/js/owl.carousel.js',
            'theme_eco_food/static/src/js/owl.carousel.min.js',
            'theme_eco_food/static/src/js/eco_food_recently_added.js',
            'theme_eco_food/static/src/js/eco_food_best_seller.js',
            'theme_eco_food/static/src/js/eco_food_featured_product.js',
            'theme_eco_food/static/src/js/eco_food_new_arrivals_new.js',
            'theme_eco_food/static/src/js/website_layout.js',
            'theme_eco_food/static/src/js/script.js',
            'theme_eco_food/static/src/js/index.js',
            'theme_eco_food/static/src/js/ecoBanners.js',
            'theme_eco_food/static/src/js/ecoClientCarousel.js',
        ],
        'web.assets_qweb': [
            'theme_eco_food/static/src/xml/snippets/'
            'eco_food_best_sellers_templates.xml',
            'theme_eco_food/static/src/xml/snippets'
            '/eco_food_featured_product_new_templates.xml',
            'theme_eco_food/static/src/xml/snippets'
            '/eco_food_new_arrivals_new_templates.xml',
            'theme_eco_food/static/src/xml/snippets/eco_food_recently_'
            'added_product_new_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
