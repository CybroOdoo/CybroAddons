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
#############################################################################
{
    'name': 'Theme AeroCourt',
    'version': '20.0.1.0.0',
    'category': 'Theme/Sports',
    'summary': 'Badminton Club Theme, Sports Club Website, Court Booking '
               'Website, Odoo20 Theme, Odoo Website Theme',
    'description': 'Theme AeroCourt gives a sports club a complete website: '
                   'a fixed glass header with a light and dark switch, a '
                   'full height hero with live open status, a court booking '
                   'calendar, coaching sessions, membership plans, a journal '
                   'with articles, a contact page and an oversized wordmark '
                   'footer. Every page is made of editable sections.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_blog', 'website_crm',
                'website_mass_mailing'],
    'data': [
        'data/crm_tag_data.xml',
        'data/blog_data.xml',
        'views/res_config_settings_views.xml',
        'views/crm_lead_views.xml',
        'views/snippets/s_aerocourt_hero.xml',
        'views/snippets/s_aerocourt_page_hero.xml',
        'views/snippets/s_aerocourt_page_hero_short.xml',
        'views/snippets/s_aerocourt_why.xml',
        'views/snippets/s_aerocourt_story.xml',
        'views/snippets/s_aerocourt_home_story.xml',
        'views/snippets/s_aerocourt_numbers.xml',
        'views/snippets/s_aerocourt_values.xml',
        'views/snippets/s_aerocourt_journey.xml',
        'views/snippets/s_aerocourt_inside.xml',
        'views/snippets/s_aerocourt_membership.xml',
        'views/snippets/s_aerocourt_testimonials.xml',
        'views/snippets/s_aerocourt_faq.xml',
        'views/snippets/s_aerocourt_contact.xml',
        'views/snippets/s_aerocourt_sessions.xml',
        'views/snippets/s_aerocourt_programs.xml',
        'views/snippets/s_aerocourt_booking.xml',
        'views/snippets/snippets.xml',
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/about_templates.xml',
        'views/booking_templates.xml',
        'views/sessions_templates.xml',
        'views/contact_templates.xml',
        'data/website_menu_data.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_aerocourt/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_aerocourt/static/src/css/fonts.css',
            'theme_aerocourt/static/src/css/icons.css',
            'theme_aerocourt/static/src/css/aerocourt.css',
            'theme_aerocourt/static/src/scss/odoo_overrides.scss',
            'theme_aerocourt/static/src/scss/header.scss',
            'theme_aerocourt/static/src/scss/blog.scss',
            'theme_aerocourt/static/src/interactions/*.js',
        ],
        'website.website_builder_assets': [
            'theme_aerocourt/static/src/website_builder/*.xml',
        ],
        'html_builder.iframe_add_dialog': [
            'theme_aerocourt/static/src/scss/snippet_preview.preview.scss',
        ],
        'website.assets_inside_builder_iframe': [
            'theme_aerocourt/static/src/scss/edit_mode.edit.scss',
        ],
    },
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
