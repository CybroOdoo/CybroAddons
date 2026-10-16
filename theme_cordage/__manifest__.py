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
    'name': 'Theme Cordage',
    'version': '19.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Premium Industrial Ropes & Rigging Theme',
    'description': 'A beautiful theme for Odoo 19 with a rugged, high-strength industrial aesthetic.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_sale', 'website_sale_wishlist', 'website_mass_mailing'],
    'data': [
        'data/base_data.xml',
        'demo/demo.xml',
        'views/snippet/snippet_groups.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/features_section.xml',
        'views/snippet/about_section.xml',
        'views/snippet/industries_grid.xml',
        'views/snippet/industry_cards_grid.xml',
        'views/snippet/certifications_band.xml',
        'views/snippet/industries_cta.xml',
        'views/snippet/products_carousel.xml',
        'views/snippet/testimonial_section.xml',
        'views/snippet/quote_section.xml',
        'views/snippet/stats_bar.xml',
        'views/snippet/story_facts.xml',
        'views/snippet/values_grid.xml',
        'views/snippet/team_grid.xml',
        'views/layout.xml',
        'views/home.xml',
        'views/about.xml',
        'views/contact.xml',
        'views/industries.xml',
        'views/shop.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_cordage/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_cordage/static/src/scss/style.scss',
            'theme_cordage/static/src/scss/shop.scss',
            'theme_cordage/static/src/js/theme.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
