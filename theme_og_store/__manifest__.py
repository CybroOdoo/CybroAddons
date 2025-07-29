# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme OG Store',
    'version': '18.0.1.0.0',
    'category': 'Theme',
    'summary': 'Design Web Pages with Theme OG',
    'description': 'Theme OG is an ideal choice for your Odoo 18.'
                   'This theme promises to offer a refreshing experience with Odoo,'
                   'enhancing its functionality and aesthetics."',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist', 'website_sale',
                'website_sale_comparison'],
    'data': [
        'security/ir.model.access.csv',
        'data/og_configuration_data.xml',
        'views/checkout.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/og_configuration_views.xml',
        'views/product_view_template.xml',
        'views/shop.xml',
        'views/snippets/best_seller_highlight.xml',
        'views/snippets/categories_highlight.xml',
        'views/snippets/choose_highlight.xml',
        'views/snippets/exclusive_category.xml',
        'views/snippets/offer_highlight.xml',
        'views/snippets/product_highlight.xml',
        'views/snippets/service_highlight.xml',
        'views/snippets/shop_highlight.xml',
        'views/snippets/subscribe_highlight.xml',
        'views/snippets/testimonials_highlight.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css",
            "/theme_og_store/static/src/css/style.css",
            "/theme_og_store/static/src/css/owl.carousel.min.css",
            "/theme_og_store/static/src/css/owl.theme.default.min.css",
            '/theme_og_store/static/src/js/owl.carousel.js',
            '/theme_og_store/static/src/js/owl.carousel.min.js',
            '/theme_og_store/static/src/js/product_category.js',
            '/theme_og_store/static/src/js/shop_highlight.js',
            '/theme_og_store/static/src/js/testimonials.js',
            '/theme_og_store/static/src/js/best_seller.js',
            '/theme_og_store/static/src/js/website_sale.js',
            '/theme_og_store/static/src/js/exclusive_categories.js',
            "/theme_og_store/static/src/xml/category_tab_content.xml",
            "/theme_og_store/static/src/xml/exclusive_tab_content.xml",
            "/theme_og_store/static/src/xml/best_seller_tab_content.xml",
            "/theme_og_store/static/src/xml/testimonial_tab_content.xml",
            "/theme_og_store/static/src/xml/shop_tab_content.xml",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
