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
    'name': 'Theme Silon',
    'version': '14.0.1.0.0',
    'summary': 'Attractive and unique front-end theme for eCommerce websites',
    'description': 'Attractive and unique front-end theme for eCommerce websites',
    'category': 'Theme/eCommerce',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'depends': ['website_mass_mailing', 'website_sale_wishlist'],
    'data': [
        'data/silon_configuration_data.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/silon_configuration.xml',
        'views/snippets/index/most_popular.xml',
        'views/snippets/index/banner.xml',
        'views/snippets/index/offer.xml',
        'views/snippets/index/features.xml',
        'views/snippets/index/journals.xml',
        'views/snippets/index/follow_us.xml',
        'views/snippets/about_us/about_us.xml',
        'views/snippets/index/featured_products.xml',
        'views/snippets/index/trending.xml',
        'views/snippets/website_rating_custom.xml',
        'views/template.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/contact_us.xml',
        'views/cart.xml',
        'views/product_page.xml',
        'views/product.xml',
        'views/views.xml'

    ],
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
