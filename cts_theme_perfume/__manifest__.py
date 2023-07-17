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
    'description': 'The Perfume theme in Odoo not only focuses on aesthetics '
                   'but also provides a seamless user experience. It is built '
                   'with a responsive design, ensuring that the website adapts '
                   'and looks visually appealing on various devices, including'
                   ' desktops, tablets, and smartphones. This responsiveness '
                   'enables businesses to reach a wider audience and deliver a '
                   'consistent brand experience across different platforms.',
    'summary': 'The Perfume-themed Odoo theme is a visually stunning and '
               'immersive design option for businesses in the fragrance '
               'industry. With its customizable snippets, carefully curated '
               'color scheme, and responsive design, this theme provides a '
               'powerful tool for creating a captivating online presence that '
               'reflects the elegance and allure of perfumes.',
    'category': 'Theme/eCommerce',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_sale_wishlist'],
    'data': [
        'views/snippets/perfume_banner.xml',
        'views/snippets/perfume_gallery.xml',
        'views/snippets/perfume_show.xml',
        'views/snippets/perfume_video.xml',
        'views/snippets/perfume_about.xml',
        'views/snippets/shop_method.xml',
        'views/snippets/new_arrival.xml',
        'data/perfume_contact_us.xml',
        'views/contact_us.xml',
        'views/shop_view.xml',
        'views/header.xml',
        'views/footer.xml',
    ],
    'assets': {
        'web.assets_frontend': [
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
            "cts_theme_perfume/static/src/scss/web.scss",
            "cts_theme_perfume/static/src/js/new_arrival.js",
        ],
        'web.assets_qweb': [
            'cts_theme_perfume/static/src/xml/new_arrivals.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
