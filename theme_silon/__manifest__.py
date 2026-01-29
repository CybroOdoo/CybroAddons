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
    'version': '15.0.1.0.0',
    'summary': 'Attractive and unique front-end theme for eCommerce websites',
    'description': 'Attractive and unique front-end theme for eCommerce websites',
    'category': 'Theme/eCommerce',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_mass_mailing', 'website_sale_wishlist'],
    'data': [
        'data/silon_configuration_data.xml',
        'security/ir.model.access.csv',
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
    'assets': {
        'web.assets_frontend': [
            '/theme_silon/static/src/css/font-awesome.min.css',
            '/theme_silon/static/src/scss/_variables.scss',
            '/theme_silon/static/src/scss/_normalize.scss',
            '/theme_silon/static/src/scss/_common.scss',
            '/theme_silon/static/src/scss/components/_buttons.scss',
            '/theme_silon/static/src/scss/layout/_footer.scss',
            '/theme_silon/static/src/scss/components/_banner.scss',
            '/theme_silon/static/src/scss/components/_product.scss',
            '/theme_silon/static/src/scss/pages/home/_offers.scss',
            '/theme_silon/static/src/scss/pages/home/_features.scss',
            '/theme_silon/static/src/scss/pages/home/_journal.scss',
            '/theme_silon/static/src/scss/pages/home/_trending.scss',
            '/theme_silon/static/src/scss/pages/home/_follow-us.scss',
            '/theme_silon/static/src/scss/pages/home/_most-popular.scss',
            '/theme_silon/static/src/scss/pages/_maincontents.scss',
            '/theme_silon/static/src/scss/pages/_product.scss',
            '/theme_silon/static/src/scss/pages/_about.scss',
            '/theme_silon/static/src/scss/layout/_header.scss',
            '/theme_silon/static/src/scss/pages/_preview.scss',
            '/theme_silon/static/src/scss/pages/_contact.scss',
            '/theme_silon/static/src/scss/pages/_cart.scss',
            '/theme_silon/static/src/js/most_popular.js',
            '/theme_silon/static/src/js/filter_price.js',
            '/theme_silon/static/src/js/featured_product.js',
            '/theme_silon/static/src/js/trending.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
