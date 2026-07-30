# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Theme Flynova',
    'version': '18.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Tour booking theme with snippets for Odoo Website',
    'description': """
Theme Flynova provides travel booking website pages, tour and hotel listings,
booking flows, and reusable website snippets for Odoo Website.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_event', 'event_sale', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_category_data.xml',
        'data/product_template_data.xml',
        'data/event_tag_data.xml',
        'data/event_event_data.xml',
        'data/event_event_ticket_data.xml',
        'data/flynova_extra_service_data.xml',
        'data/flynova_traveller_photo_data.xml',
        'views/layout_templates.xml',
        'views/homepage_templates.xml',
        'views/event_event_views.xml',
        'views/event_templates.xml',
        'views/registration_templates.xml',
        'views/other_pages.xml',
        'views/tour_templates.xml',
        'views/hotel_templates.xml',
        'views/product_template_views.xml',
        'views/flynova_traveller_photo_views.xml',
        'views/tour_hotel_menus.xml',
        'views/payment_templates.xml',
        'views/snippets/s_flynova_hero.xml',
        'views/snippets/s_flynova_explore_hero.xml',
        'views/snippets/s_flynova_explore_highlights.xml',
        'views/snippets/s_flynova_destinations.xml',
        'views/snippets/s_flynova_featured_tours.xml',
        'views/snippets/s_flynova_hotels.xml',
        'views/snippets/s_flynova_discover.xml',
        'views/snippets/s_flynova_about.xml',
        'views/snippets/s_flynova_features.xml',
        'views/snippets/s_flynova_activities.xml',
        'views/snippets/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_flynova/static/src/scss/primary_variables.scss',
            'theme_flynova/static/src/css/theme.css',
            'theme_flynova/static/src/xml/theme_flynova.xml',
            'theme_flynova/static/src/js/theme_flynova.js',
        ],
        'website.assets_wysiwyg': [
            'theme_flynova/static/src/scss/primary_variables.scss',
            'theme_flynova/static/src/css/theme.css',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
