# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM(<https://www.cybrosys.com>)
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
    'name': 'Theme Zen Dark',
    'description': 'Design Web Pages with Theme Zen Dark',
    'summary': 'Design Web Pages with Theme Zen Dark',
    'category': 'Theme/Corporate',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'website_blog', 'website_sale_wishlist'],
    'data': [
        'views/index/index_banner.xml',
        'views/index/index_about.xml',
        'views/index/index_testinomial.xml',
        'views/index/index_blog.xml',
        'views/index/index_partners.xml',
        'views/index/index_recent.xml',
        'views/index/index_video.xml',
        'views/about/about.xml',
        'views/service/service.xml',
        'views/portfolio/portfolio.xml',
        'views/recent_post.xml',
        'views/contact.xml',
        'views/blog.xml',
        'views/blog_details.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdn.jsdelivr.net/npm/'
            '@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/'
            'dist/jquery.fancybox.min.css',
            '/theme_zen_dark/static/src/css/animate.min.css',
            '/theme_zen_dark/static/src/css/foundation.min.css',
            '/theme_zen_dark/static/src/css/owl.carousel.min.css',
            '/theme_zen_dark/static/src/css/owl.theme.default.min.cs',
            '/theme_zen_dark/static/src/css/style.css',
            '/theme_zen_dark/static/src/css/style2.css',
            '/theme_zen_dark/static/src/js/foundation.min.js',
            '/theme_zen_dark/static/src/js/owl.carousel.js',
            '/theme_zen_dark/static/src/js/owl.carousel.min.js',
            '/theme_zen_dark/static/src/js/custom.js',
            '/theme_zen_dark/static/src/js/custom_nav.js',
            '/theme_zen_dark/static/src/js/custom_get_elements.js',
        ]
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
