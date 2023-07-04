# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I(<https://www.cybrosys.com>)
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
    'name': 'Theme Perfume',
    'description': 'Theme Perfume is a fragrance management module in the Odoo'
                   'platform. It offers a comprehensive solution for businesses'
                   'businesses involved in the perfume industry to effectively'
                   'manage their fragrance products more stylish.',
    'summary': 'Design Web Pages with theme Perfume',
    'category': 'Theme/eCommerce',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_sale_wishlist'],
    'data': [
        'data/perfume_contact_us_data.xml',
        'views/snippets/perfume_banner_templates.xml',
        'views/snippets/perfume_gallery_templates.xml',
        'views/snippets/perfume_show_templates.xml',
        'views/snippets/perfume_video_templates.xml',
        'views/snippets/perfume_about_templates.xml',
        'views/snippets/shop_method_templates.xml',
        'views/snippets/new_arrival_templates.xml',
        'views/contact_us_templates.xml',
        'views/header_templates.xml',
        'views/footer_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'cts_theme_perfume/static/src/xml/new_arrivals_templates.xml',
            "cts_theme_perfume/static/src/css/all.css",
            "cts_theme_perfume/static/src/css/animate.min.css",
            "cts_theme_perfume/static/src/css/aos.css",
            "cts_theme_perfume/static/src/css/bootstrap.min.css",
            "cts_theme_perfume/static/src/css/flaticon.css",
            "cts_theme_perfume/static/src/css/fontawesome-all.min.css",
            "cts_theme_perfume/static/src/css/lightslider.min.css",
            "cts_theme_perfume/static/src/css/nice-select.css",
            "cts_theme_perfume/static/src/css/price_rangs.css",
            "cts_theme_perfume/static/src/css/slick.css",
            "cts_theme_perfume/static/src/css/slick.min.css",
            "cts_theme_perfume/static/src/css/slick-theme.min.css",
            "cts_theme_perfume/static/src/css/slicknav.css",
            "cts_theme_perfume/static/src/css/style.css",
            "cts_theme_perfume/static/src/css/swiper.min.css",
            "cts_theme_perfume/static/src/css/themify-icons.css",
            "cts_theme_perfume/static/src/js/new_arrival.js",
            "cts_theme_perfume/static/src/js/bootstrap.min.js",
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
