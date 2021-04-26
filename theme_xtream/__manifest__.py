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
    'name': 'Theme Xtream Fashion',
    'description': 'Design eCommerce Website with Theme Xtream Fashion',
    'summary': 'Theme Xtream Fashion',
    'category': 'Theme/eCommerce',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/assets.xml',
        'views/categories.xml',
        'views/clear_cart.xml',
        'views/contact_us.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/layout.xml',
        'views/price_filter.xml',
        'views/product_view.xml',
        'views/shop.xml',
        'views/snippets/amazing.xml',
        'views/snippets/arrivals_demo.xml',
        'views/snippets/new_arrivals.xml',
        'views/snippets/discount.xml',
        'views/snippets/main_banner.xml',
        'views/snippets/main_product.xml',
        'views/snippets/map.xml',
        'views/snippets/testimonial.xml',
    ],
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
