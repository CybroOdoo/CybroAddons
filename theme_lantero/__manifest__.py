# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Lantero',
    'version': '18.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Premium Jewelry Website Theme',
    'description': 'A stunning jewelry theme for Odoo 19 with a premium aesthetic.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_sale', 'website_blog', 'website_sale_wishlist', 'website_mass_mailing'],
    'data': [
        'views/snippet/snippet_groups.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/features_section.xml',
        'views/snippet/about_section.xml',
        'views/snippet/categories_grid.xml',
        'views/snippet/products_carousel.xml',
        'views/snippet/statement_banner.xml',
        'views/snippet/trends_grid.xml',
        'views/snippet/testimonial_section.xml',
        'views/snippet/instagram_feed.xml',
        'views/snippet/blog_posts_snippet.xml',
        'views/snippet/contact_snippets.xml',
        'views/snippet/track_lookup.xml',
        'views/layout.xml',
        'views/shop_templates.xml',
        'views/home.xml',
        'views/about.xml',
        'views/blog.xml',
        'views/contact.xml',
        'views/track_order.xml',
        'data/demo.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_lantero/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_lantero/static/src/scss/style.scss',
            'theme_lantero/static/src/scss/shop.scss',
            'theme_lantero/static/src/js/theme.js',
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
