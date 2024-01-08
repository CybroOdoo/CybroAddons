# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R(<https://www.cybrosys.com>)
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
    'name': 'Theme WatchHut',
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Theme WatchHut is an attractive and modern eCommerce Website'
               ' theme',
    'description': 'Theme WatchHut is an attractive and modern eCommerce '
                   'Website theme.The theme is a very user-friendly and is '
                   'suitable for your eCommerce website.It is the most powerful'
                   ', easy to use theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'website_sale'],
    'data': [
            'views/about_page.xml',
            'views/contact_us.xml',
            'views/footer.xml',
            'views/product_view.xml',
            'views/shop.xml',
            'views/snippets/gallery.xml',
            'views/snippets/heading.xml',
            'views/snippets/shop_button.xml',
            'views/header.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_watchhut/static/src/css/style.css',
            '/theme_watchhut/static/src/css/font-awesome.min.css',
            '/theme_watchhut/static/src/js/custom.js',
            'https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;'
            '0,500;0,600;0,700;1,400;1,500;1,600;1,700&amp;display=swap',
            'https://fonts.googleapis.com/css2?family=Cinzel+Decorative:'
            'wght@400;700;900&amp;display=swap',
        ]
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
