# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################

{
    'name': 'Theme Reflect',
    'version': '19.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Minimal editorial e-commerce theme with snippets',
    'description': """
Minimal editorial e-commerce theme with snippets           
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'website_mass_mailing'],
    'data': [
        'data/product_public_category_data.xml',
        'views/pages.xml',
        'views/shop_product_card_template.xml',
        'views/layout.xml',
        'views/product_templates.xml',
        'views/dynamic_snippets.xml',
        'views/checkout_templates.xml',
        'views/shop_templates.xml',
        'views/snippet/reflect_categories_snippet.xml',
        'views/snippet/reflect_editorial_snippet.xml',
        'views/snippet/reflect_feature_snippet.xml',
        'views/snippet/reflect_group_snippet.xml',
        'views/snippet/reflect_newsteller_snippet.xml',
        'views/snippet/reflect_products_snippet.xml',
        'views/snippet/reflect_style_stories.xml',
        'views/snippet/s_reflect_shopping.xml',
        'views/snippet/snippet_group.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_reflect/static/src/css/theme.css',
            'theme_reflect/static/src/css/theme_additions.css',
            'theme_reflect/static/src/css/shop.scss',
            'theme_reflect/static/src/scss/reflect_shop.scss',
            'theme_reflect/static/src/css/product.scss',
            'theme_reflect/static/src/css/checkout.scss',
            'theme_reflect/static/src/js/theme.js',
            'theme_reflect/static/src/js/new_in_wishlist_widget.js',
        ],
        'website.assets_wysiwyg': [
            'theme_reflect/static/src/css/snippet_editor.css',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
