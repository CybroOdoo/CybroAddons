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
    'name': 'Theme Autofly',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Design eCommerce Website with Theme AutoFly',
    'description': 'Theme Autofly module provide attractive and unique '
                   'front end theme mainly suitable for eCommerce website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_blog', 'website_sale_wishlist'],
    'data': [
        'security/ir.model.access.csv',
        'data/theme_autofly_sequence.xml',
        'views/car_type_views.xml',
        'views/car_brand_views.xml',
        'views/car_garage_views.xml',
        'views/blog_page_templates.xml',
        'views/portfolio_templates.xml',
        'views/about_us_templates.xml',
        'views/footer_templates.xml',
        'views/header_templates.xml',
        'views/contact_us_templates.xml',
        'views/team_templates.xml',
        'views/service_templates.xml',
        'views/snippets/snippet_templates.xml',
        'views/snippets/popular_model_templates.xml',
        'views/snippets/blog_templates.xml',
        'views/snippets/find_car_templates.xml',
        'views/snippets/partners_templates.xml',
        'views/snippets/testimonial_templates.xml',
        'views/snippets/choose_us_templates.xml',
        'views/snippets/banner_templates.xml',
        'views/snippets/search_templates.xml',
        'views/service_booking_views.xml',
        'views/product_template_views.xml',
        'views/testimonial_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_autofly/static/src/xml/blog_snippet_templates.xml',
            '/theme_autofly/static/src/xml/testimonial_snippet_templates.xml',
            '/theme_autofly/static/src/js/service_products.js',
            '/theme_autofly/static/src/js/car_garage.js',
            'theme_autofly/static/src/css/style.css',
            '/theme_autofly/static/src/js/owl.carousel.js',
            '/theme_autofly/static/src/js/owl.carousel.min.js',
            'theme_autofly/static/src/css/owl.theme.default.min.css',
            '/theme_autofly/static/src/js/owl.carousel.js',
            '/theme_autofly/static/src/js/product_tab.js',
            '/theme_autofly/static/src/js/find_car.js',
            '/theme_autofly/static/src/js/search.js',
            '/theme_autofly/static/src/js/blog.js',
            '/theme_autofly/static/src/js/testimonial.js',
            '/theme_autofly/static/src/js/all_type.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
