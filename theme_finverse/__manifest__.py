# -*- coding: utf-8 -*-
############################################################################-
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
############################################################################-
{
    'name': 'Theme Finverse',
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': 'Modern Finance & Consulting Website Theme',
    'description': 'Modern Finance & Consulting Website Theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_crm'],
    'data': [
        'data/website_menus.xml',
        'views/snippet/snippets.xml',
        'views/snippet/s_hero.xml',
        'views/snippet/s_stats.xml',
        'views/snippet/s_highlights.xml',
        'views/snippet/s_why.xml',
        'views/snippet/s_services.xml',
        'views/snippet/s_testimonials.xml',
        'views/snippet/s_s_contact.xml',
        'views/snippet/s_about_hero.xml',
        'views/snippet/s_about_story.xml',
        'views/snippet/s_stats_about.xml',
        'views/snippet/s_about_values.xml',
        'views/snippet/s_team.xml',
        'views/snippet/s_services_hero.xml',
        'views/snippet/s_services_list.xml',
        'views/snippet/s_approach.xml',
        'views/snippet/s_cases.xml',
        'views/snippet/s_industries_hero.xml',
        'views/snippet/s_industries_grid.xml',
        'views/snippet/s_value.xml',
        'views/snippet/s_insights_hero.xml',
        'views/snippet/s_insights_list.xml',
        'views/snippet/s_contact_hero.xml',
        'views/snippet/s_contact_form.xml',
        'views/snippet/s_contact_faq.xml',
        'views/snippet/s_contact_faq_item.xml',
        'views/layout.xml',
        'views/home.xml',
        'views/about.xml',
        'views/services.xml',
        'views/industries.xml',
        'views/insights.xml',
        'views/contact.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_finverse/static/src/scss/style.scss',
            'theme_finverse/static/src/js/theme.js',
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
