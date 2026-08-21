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
    "name": "Theme University",
    "version": "19.0.1.0.0",
    "category": "Theme/Education",
    "sequence": 110,
    "summary": "A premium academic theme for Odoo 19 matching the Axion University design.",
    "description": "A premium academic theme for Odoo 19 matching the Axion University design.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "website_crm", "website_event"],
    "data": [
        "data/website_menu_data.xml",
        "data/crm_data.xml",
        "views/layout_templates.xml",
        "views/snippets/snippet_groups.xml",
        "views/snippets/university_hero.xml",
        "views/snippets/university_ticker.xml",
        "views/snippets/university_programs.xml",
        "views/snippets/university_why_us.xml",
        "views/snippets/university_stats.xml",
        "views/snippets/university_events.xml",
        "views/snippets/university_testimonials.xml",
        "views/snippets/university_research.xml",
        "views/snippets/university_gallery.xml",
        "views/snippets/university_cta.xml",
        "views/snippets/university_news.xml",
        "views/snippets/university_logos.xml",
        "views/snippets/university_inner_hero.xml",
        "views/snippets/university_schools.xml",
        "views/snippets/university_quick_links.xml",
        "views/snippets/university_faculty.xml",
        "views/snippets/university_calendar.xml",
        "views/pages_templates.xml",
        "views/graduate_templates.xml",
        "views/programs_templates.xml",
        "views/events_templates.xml",
        "views/extra_pages_templates.xml",
        "views/contactus_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_university/static/src/scss/theme.scss",
            "theme_university/static/src/js/theme.js",
        ],
    },
    "images": [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
