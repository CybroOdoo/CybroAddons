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
    'name': 'Theme Classic Store',
    'description': 'Theme Classic Store for Odoo Website and e-Commerce',
    'summary': 'Theme Classic Store is an attractive eCommerce Website theme. '
               'The theme comes with many useful and stylish snippets',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Theme/eCommerce',
    'depends': ['website_blog', 'website_sale_wishlist', 'website_sale_comparison'],
    'data': [
        'views/classic_store_config.xml',
        'data/classic_store_config_data.xml',
        'security/ir.model.access.csv',
        'views/layout.xml',
        'views/assets.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/contact_us.xml',
        'views/blog.xml',
        'views/shop.xml',
        'views/shop_sidebar.xml',
        'views/404.xml',
        'views/product_view.xml',
        'views/product_view_inherits.xml',
        'views/snippets/about.xml',
        'views/snippets/banner.xml',
        'views/snippets/categories.xml',
        'views/snippets/listing.xml',
        'views/snippets/package.xml',
        'views/snippets/team.xml',
        'views/snippets/counter.xml',
        'views/snippets/sub_header.xml',
        'views/snippets/search.xml',
        'views/snippets/trending.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
