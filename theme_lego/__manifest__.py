# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Lego',
    'description': 'Design Web Pages with Theme Lego',
    'summary': 'Design Web Pages with Theme Lego',
    'category': 'Theme/Corporate',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'views/assets.xml',
        'views/layout.xml',
        'views/footer.xml',
        'views/shop.xml',
        'views/add_to_cart.xml',
        'views/cart.xml',
        'views/payment.xml',
        'views/login.xml',
        'views/address.xml',
        'views/header.xml',
        'views/deal_back.xml',
        'views/snippets/deal.xml',
        'views/snippets/cart_banner.xml',
        'views/snippets/index.xml',
        'views/snippets/banner.xml',
        'views/snippets/contact.xml',
        'views/snippets/map.xml',
        'views/snippets/login.xml'

    ],
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
