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
    'name': 'Theme Diva',
    'description': 'Design Web Pages with Theme Diva',
    'summary': 'Design Web Pages with Theme Diva',
    'category': 'Theme/Corporate',
    'version': '14.0.1.1.1',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_blog'],
    'data': [
        'views/featured_configuration.xml',
        'security/ir.model.access.csv',
        'data/featured_product.xml',
        'views/assets.xml',
        'views/views.xml',
        'views/customize.xml',
        'views/layout.xml',
        'views/myaccount.xml',
        'views/shop1.xml',
        'views/product_view.xml',
        'views/cart_view.xml',
        'views/checkout.xml',
        'views/contact.xml',
        'views/index/index_banner.xml',
        'views/index/index_main_product.xml',
        'views/index/index_featured_product.xml',
        'views/index/index_demo.xml',
        'views/index/index_subscribe.xml',
        'views/index 2/banner.xml',
        'views/index 2/popular_product.xml',
        'views/index 2/Featured_product.xml',
        'views/index 2/testimonial.xml',
        'views/index 2/offer.xml',
        'views/index 2/index2_blog.xml',
        'views/index 3/index3_banner.xml',
        'views/index 3/index3_product.xml',
        'views/index 3/index3_store.xml',
        'views/index 3/index3_gallery.xml',
        'views/index 3/index3_blog.xml',
        'views/landing_page/landing_features.xml',
        'views/landing_page/landing_demo.xml',
        'views/landing_page/landing_banner.xml',
        'views/landing_page/landing_sponsored.xml',
        'views/landing_page/landing_testimonial.xml',
        'views/landing_page/landing_subscribe.xml',
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
