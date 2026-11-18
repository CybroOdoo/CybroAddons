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
    'name': 'Theme Propelle',
    'version': '20.0.1.0.0',
    'category': 'Theme/Real Estate',
    'summary': 'A website theme for a real estate brokerage: listings to buy '
               'and rent, new developments, valuations and viewing requests.',
    'description': 'Theme Propelle gives a real estate brokerage a complete '
                   'website: a floating glass header, a hero with a Buy / '
                   'Rent search panel, published listings and developments '
                   'managed from the backend, filters, favourites, a details '
                   'dialog, mortgage and rent calculators, a valuation '
                   'request and a four step request of viewings sent to CRM '
                   'as leads. Pages are built from editable snippets.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_crm', 'website_mass_mailing', 'crm'],
    'data': [
        'security/ir.access.csv',
        'data/propelle_city_data.xml',
        'views/propelle_property_views.xml',
        'views/propelle_city_views.xml',
        'views/propelle_project_views.xml',
        'views/snippets/s_propelle_about_hero.xml',
        'views/snippets/s_propelle_alert.xml',
        'views/snippets/s_propelle_band.xml',
        'views/snippets/s_propelle_careers.xml',
        'views/snippets/s_propelle_cities.xml',
        'views/snippets/s_propelle_contact.xml',
        'views/snippets/s_propelle_faq.xml',
        'views/snippets/s_propelle_faq_grid.xml',
        'views/snippets/s_propelle_features.xml',
        'views/snippets/s_propelle_fees.xml',
        'views/snippets/s_propelle_hero.xml',
        'views/snippets/s_propelle_history.xml',
        'views/snippets/s_propelle_intro.xml',
        'views/snippets/s_propelle_mortgage.xml',
        'views/snippets/s_propelle_offices.xml',
        'views/snippets/s_propelle_page_hero.xml',
        'views/snippets/s_propelle_praise.xml',
        'views/snippets/s_propelle_process.xml',
        'views/snippets/s_propelle_quote.xml',
        'views/snippets/s_propelle_rent_calc.xml',
        'views/snippets/s_propelle_reviews.xml',
        'views/snippets/s_propelle_routes.xml',
        'views/snippets/s_propelle_sold.xml',
        'views/snippets/s_propelle_split_card.xml',
        'views/snippets/s_propelle_split_cta.xml',
        'views/snippets/s_propelle_spotlight.xml',
        'views/snippets/s_propelle_steps.xml',
        'views/snippets/s_propelle_steps_dark.xml',
        'views/snippets/s_propelle_steps_vertical.xml',
        'views/snippets/s_propelle_team.xml',
        'views/snippets/s_propelle_valuation.xml',
        'views/snippets/s_propelle_values.xml',
        'views/snippets/snippets.xml',
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/about_templates.xml',
        'views/sell_templates.xml',
        'views/contact_templates.xml',
        'views/listing_templates.xml',
        'views/projects_templates.xml',
        'views/booking_templates.xml',
        'data/website_menu_data.xml',
    ],
    'demo': [
        'data/propelle_property_demo.xml',
        'data/propelle_project_demo.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_propelle/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_propelle/static/src/css/base.css',
            'theme_propelle/static/src/css/fonts.css',
            'theme_propelle/static/src/css/icons.css',
            'theme_propelle/static/src/css/propelle.css',
            'theme_propelle/static/src/scss/odoo_overrides.scss',
            'theme_propelle/static/src/scss/header.scss',
            'theme_propelle/static/src/js/propelle_core.js',
            'theme_propelle/static/src/js/propelle_header.js',
            'theme_propelle/static/src/js/propelle_listings.js',
            'theme_propelle/static/src/js/propelle_forms.js',
            'theme_propelle/static/src/js/propelle_booking.js',
        ],
        'website.assets_inside_builder_iframe': [
            'theme_propelle/static/src/scss/edit_mode.edit.scss',
        ],
        'html_builder.iframe_add_dialog': [
            'theme_propelle/static/src/scss/edit_mode.edit.scss',
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

