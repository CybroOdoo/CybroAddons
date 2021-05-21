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
    'name': 'Theme Perfume',
    'description': 'Design Web Pages with theme Perfume',
    'summary': 'Design Web Pages with theme Perfume',
    'category': 'Theme/eCommerce',
    'version': '14.0.1.0.0',
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
            'views/product_views.xml',
            'views/contact_us.xml',
            'views/header.xml',
            'views/footer.xml',
            'views/assets.xml',
            'views/layout.xml',
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
