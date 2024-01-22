# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions,(odoo@cybrosys.com)
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
    'name': 'Theme Rozz',
    'version': '17.0.1.0.0',
    'category': 'Theme/corporate',
    'summary': 'Design Web Pages with Theme Rozz',
    'description': 'Theme Rozz is a attractive and unique front-end theme '
                   'mainly suitable for Corporate website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog', 'website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'views/header_templates.xml',
        'views/footer_templates.xml',
        'views/contact_us_templates.xml',
        'views/blog_templates.xml',
        'views/snippets/rozz_banner.xml',
        'views/snippets/rozz_services.xml',
        'views/snippets/rozz_team.xml',
        'views/snippets/rozz_aboutus.xml',
        'views/snippets/about_us.xml',
        'views/snippets/services_page.xml',
        'views/snippets/rozz_subscribe.xml',
        'views/snippets/portfolio_page.xml',
        'views/snippets/portfolio_details.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "/cts_theme_rozz/static/src/css/style.css",
            "/cts_theme_rozz/static/src/css/meanmenu.css",
            "/cts_theme_rozz/static/src/css/responsive.css",
            "/cts_theme_rozz/static/src/css/boxicons.min.css",
            "/cts_theme_rozz/static/src/css/magnific-popup.css",
            "/cts_theme_rozz/static/src/css/nice-select.css",
            "/cts_theme_rozz/static/src/css/odometer.css",
            "/cts_theme_rozz/static/src/css/owl.theme.default.min.css",
            "/cts_theme_rozz/static/src/js/bootstrap.bundle.js",
            "/cts_theme_rozz/static/src/js/bootstrap.bundle.js.map",
            "/cts_theme_rozz/static/src/js/bootstrap.bundle.min.js.map",
            "/cts_theme_rozz/static/src/js/bootstrap.js.map",
            "/cts_theme_rozz/static/src/js/bootstrap.min.js.map",
            "/cts_theme_rozz/static/src/js/form-validator.min.js",
            "/cts_theme_rozz/static/src/js/jquery.ajaxchimp.min.js",
            "/cts_theme_rozz/static/src/js/jquery.appear.js",
            "/cts_theme_rozz/static/src/js/jquery.magnific-popup.min.js",
            "/cts_theme_rozz/static/src/js/jquery.meanmenu.js",
            "/cts_theme_rozz/static/src/js/jquery.nice-select.min.js",
            "/cts_theme_rozz/static/src/js/odometer.min.js",
            "/cts_theme_rozz/static/src/js/owl.carousel.min.js",
            "/cts_theme_rozz/static/src/js/popper.min.js",
            "/cts_theme_rozz/static/src/js/thumb-slide.js",
            "https://fonts.googleapis.com/css2?family=Karla:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;1,300;1,500&amp;family=Montserrat&amp;display=swap"
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
