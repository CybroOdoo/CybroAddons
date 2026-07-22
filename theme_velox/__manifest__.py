# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Velox Sports Theme',
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Dark, high-performance sports eCommerce theme with custom snippets and shop routes.',
    'description': 'Dark, high-performance sports eCommerce theme with custom snippets and shop routes.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale_wishlist'],
    'data': [
        'data/product_public_category_data.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/confirmation_template.xml',
        'views/snippets/velox_product_card.xml',
        'views/snippets/s_velox_hero.xml',
        'views/snippets/s_velox_features.xml',
        'views/snippets/s_velox_new_arrivals.xml',
        'views/snippets/s_velox_sale_products.xml',
        'views/snippets/s_velox_sport_categories.xml',
        'views/snippets/s_velox_club_banner.xml',
        'views/snippets/s_velox_trending_grid.xml',
        'views/snippets/s_velox_seasonal_banner.xml',
        'views/snippets/s_velox_testimonials.xml',
        'views/snippets/s_velox_stats.xml',
        'views/snippets/s_velox_featured_product.xml',
        'views/snippets/snippet_groups.xml',
        'views/pages.xml',
        'views/shop_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            ('prepend', 'theme_velox/static/src/scss/variables.scss'),
            'theme_velox/static/src/scss/theme.scss',
            'theme_velox/static/src/scss/snippets.scss',
            'theme_velox/static/src/scss/shop.scss',
            'theme_velox/static/src/scss/mobile.scss',
            'theme_velox/static/src/js/theme.js'
        ],
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
