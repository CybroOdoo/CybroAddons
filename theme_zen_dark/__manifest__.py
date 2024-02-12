# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K (odoo@cybrosys.com)
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
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Design Web Pages with theme zen dark',
    'description': 'Design web pages with the Theme Zen Dark by embracing '
                   'minimalism,balancing typography and visuals,'
                   ' and optimizing responsiveness for a serene and visually'
                   ' appealing browsing experience',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog', 'website_sale_wishlist'],
    'data': [
        'views/index/index_banner.xml',
        'views/index/index_about.xml',
        'views/index/index_testimonial.xml',
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
        'views/shop.xml',
        'views/blog_details.xml',
        'views/website_templates.xml',
        'views/snippets/snippets.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.css',
            '/theme_zen_dark/static/src/css/animate.min.css',
            '/theme_zen_dark/static/src/css/foundation.min.css',
            '/theme_zen_dark/static/src/css/owl.theme.default.min.css',
            '/theme_zen_dark/static/src/css/style.css',
            '/theme_zen_dark/static/src/css/style2.css',
            '/theme_zen_dark/static/lib/js/foundation.min.js',
            '/theme_zen_dark/static/src/js/custom_nav.js',
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
