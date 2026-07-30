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
    'name': 'Tennis Court Theme',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Professional Tennis Club, Sports Complex, and Country Club Theme',
    'description': """A premium, highly interactive, and fully responsive sports theme
designed specifically for tennis clubs, sports complexes, racket clubs, coaching academies,
and country clubs to manage and showcase their courts, training facilities, membership pricing
plans, and coaching programs.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail'],
    'data': [
        'data/theme_website_menu_data.xml',
        'views/layout.xml',
        'views/snippet/about_hero.xml',
        'views/snippet/about_mission.xml',
        'views/snippet/about_values.xml',
        'views/snippet/about_leadership.xml',
        'views/snippet/facilities_hero.xml',
        'views/snippet/facilities_main_courts.xml',
        'views/snippet/facilities_training.xml',
        'views/snippet/facilities_amenities.xml',
        'views/snippet/programs_hero.xml',
        'views/snippet/programs_junior.xml',
        'views/snippet/programs_adult.xml',
        'views/snippet/coaches_hero.xml',
        'views/snippet/coaches_head_coach.xml',
        'views/snippet/coaches_senior.xml',
        'views/snippet/coaches_fitness.xml',
        'views/snippet/pricing_hero.xml',
        'views/snippet/pricing_benefits.xml',
        'views/snippet/pricing_faq.xml',
        'views/snippet/contact_header.xml',
        'views/snippet/contact_section.xml',
        'views/snippet/snippet_groups.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/partners_strip.xml',
        'views/snippet/about_intro.xml',
        'views/snippet/features_grid.xml',
        'views/snippet/stats_banner.xml',
        'views/snippet/programs_grid.xml',
        'views/snippet/coaches_grid.xml',
        'views/snippet/pricing_cards.xml',
        'views/snippet/testimonials.xml',
        'views/snippet/cta_banner.xml',
        'views/snippet/tour_hero.xml',
        'views/snippet/tour_video.xml',
        'views/snippet/tour_grid.xml',
        'views/snippet/tour_cta.xml',
        'views/snippet/join_application.xml',
        'views/home.xml',
        'views/about.xml',
        'views/facilities.xml',
        'views/programs.xml',
        'views/coaches.xml',
        'views/pricing.xml',
        'views/contact.xml',
        'views/tour.xml',
        'views/join.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_tennis_court/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_tennis_court/static/src/scss/style.scss',
            'theme_tennis_court/static/src/js/contact_form_validation.js',
            'theme_tennis_court/static/src/js/theme.js',
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
