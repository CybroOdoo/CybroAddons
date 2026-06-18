# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Beauty Shop Theme',
    'version': '19.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Beauty Shop Theme is an advanced eCommerce theme crafted for beauty and wellness stores. '
               'It transforms your online shop into a sophisticated, modern platform with a sleek '
               'design and premium UI/UX.',
    'description': 'Stunning eCommerce beauty shop theme inspired by Glowing',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_sale'],
    'data': [
        'data/website_menu_data.xml',
        'views/shop_templates.xml',
        'views/contact_page_template.xml',
        'views/checkout_template.xml',
        'views/cart_template.xml',
        'views/about_template.xml',
        'views/product_template.xml',
        'views/home.xml',
        'views/success_template.xml',
        'views/header.xml',
        'views/thank_you_template.xml',
        'views/footer.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_beauty_shop/static/src/css/style.css',
            'theme_beauty_shop/static/src/js/shop.js',
        ],
    },
    'images': ['static/description/banner.jpg',
               'static/description/thumbnail.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
