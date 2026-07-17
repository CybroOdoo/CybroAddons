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
    "name": "Tennis Court Theme",
    "version": "18.0.1.0.0",
    "category": "Theme/Corporate",
    "sequence": 100,
    "summary": "Professional Tennis Club, Sports Complex, and Country Club Theme",
    "description": "A premium, highly interactive, and fully responsive sports theme designed specifically for tennis clubs, sports complexes, racket clubs, coaching academies, and country clubs to manage and showcase their courts, training facilities, membership pricing plans, and coaching programs.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "mail"],
    "data": [
        "data/website_menu.xml",
        "views/layout_templates.xml",
        "views/snippets/s_about_hero.xml",
        "views/snippets/s_about_history.xml",
        "views/snippets/s_about_intro.xml",
        "views/snippets/s_about_leadership.xml",
        "views/snippets/s_about_mission.xml",
        "views/snippets/s_about_values.xml",
        "views/snippets/s_coaches_fitness.xml",
        "views/snippets/s_coaches_grid.xml",
        "views/snippets/s_coaches_head_coach.xml",
        "views/snippets/s_coaches_hero.xml",
        "views/snippets/s_coaches_senior.xml",
        "views/snippets/s_contact_header.xml",
        "views/snippets/s_contact_section.xml",
        "views/snippets/s_cta_banner.xml",
        "views/snippets/s_facilities_amenities.xml",
        "views/snippets/s_facilities_hero.xml",
        "views/snippets/s_facilities_main_courts.xml",
        "views/snippets/s_facilities_training.xml",
        "views/snippets/s_features_grid.xml",
        "views/snippets/s_hero_banner.xml",
        "views/snippets/s_join_application.xml",
        "views/snippets/s_partners_strip.xml",
        "views/snippets/s_pricing_benefits.xml",
        "views/snippets/s_pricing_cards.xml",
        "views/snippets/s_pricing_faq.xml",
        "views/snippets/s_pricing_hero.xml",
        "views/snippets/s_programs_adult.xml",
        "views/snippets/s_programs_grid.xml",
        "views/snippets/s_programs_hero.xml",
        "views/snippets/s_programs_junior.xml",
        "views/snippets/s_snippet_groups.xml",
        "views/snippets/s_stats_banner.xml",
        "views/snippets/s_testimonials.xml",
        "views/snippets/s_tour_cta.xml",
        "views/snippets/s_tour_grid.xml",
        "views/snippets/s_tour_hero.xml",
        "views/snippets/s_tour_video.xml",
        "views/about_templates.xml",
        "views/coaches_templates.xml",
        "views/contact_templates.xml",
        "views/facilities_templates.xml",
        "views/home_templates.xml",
        "views/join_templates.xml",
        "views/pricing_templates.xml",
        "views/programs_templates.xml",
        "views/tour_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "theme_tennis_court/static/src/scss/primary_variables.scss",
        ],
        "web.assets_frontend": [
            "theme_tennis_court/static/src/scss/theme.scss",
            "theme_tennis_court/static/src/js/contact_form_validation.js",
            "theme_tennis_court/static/src/js/theme.js",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
