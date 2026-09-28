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
    'name': 'Theme University',
    'version': '18.0.1.0.0',
    'category': 'Theme/Education',
    'summary': 'Premium University Website Theme',
    'description': 'A beautiful, modern, and production-ready academic theme for Odoo 18.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'website', 'website_event', 'website_mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'data/mailing_list_data.xml',
        'data/apply_demo_data.xml',
        'data/website_menu_data.xml',
        'views/admissions_backend_views.xml',
        'views/application_backend_views.xml',
        'views/application_form_templates.xml',
        'views/snippet/snippet_groups.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/ticker.xml',
        'views/snippet/programs_section.xml',
        'views/snippet/why_choose_us.xml',
        'views/snippet/stats_section.xml',
        'views/snippet/events_section.xml',
        'views/snippet/testimonials.xml',
        'views/snippet/research_section.xml',
        'views/snippet/gallery_section.xml',
        'views/snippet/cta_section.xml',
        'views/snippet/news_section.xml',
        'views/snippet/logos_bar.xml',
        'views/snippet/page_sections.xml',
        'views/snippet/common_snippets.xml',
        'views/layout.xml',
        'views/home.xml',
        'views/about.xml',
        'views/academics.xml',
        'views/campus_life.xml',
        'views/research.xml',
        'views/contact.xml',
        'views/undergraduate.xml',
        'views/graduate.xml',
        'views/online_learning.xml',
        'views/research_centers.xml',
        'views/housing_dining.xml',
        'views/clubs_orgs.xml',
        'views/athletics.xml',
        'views/health_wellness.xml',
        'views/events_page.xml',
        'views/apply.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_university/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_university/static/src/scss/style.scss',
            'theme_university/static/src/js/theme.js',
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
