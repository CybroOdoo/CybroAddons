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
    'name': 'Theme Lumiee Events',
    'version': '18.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Elegant Wedding Planner, Event Management, and Corporate Celebrations Theme',
    'description': 'An elegant, modern, and highly polished premium event management theme designed for wedding planners, event coordinators, caterers, corporate organizers, and creative agencies to present their planning services, comparison packages, interactive portfolios, and contact channels.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail'],
    'data': [
        'data/website_menu_data.xml',
        'views/layout.xml',
        'views/snippet/snippet_groups.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/brochure_section.xml',
        'views/snippet/pricing_cards_home.xml',
        'views/snippet/gallery_grid_home.xml',
        'views/snippet/contact_form_home.xml',
        'views/snippet/faq_section.xml',
        'views/snippet/page_hero.xml',
        'views/snippet/services_grid.xml',
        'views/snippet/process_steps.xml',
        'views/snippet/gallery_filter.xml',
        'views/snippet/pricing_cards.xml',
        'views/snippet/comparison_table.xml',
        'views/snippet/contact_info_cards.xml',
        'views/snippet/contact_form.xml',
        'views/home.xml',
        'views/services.xml',
        'views/gallery.xml',
        'views/pricing.xml',
        'views/contact.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_lumiee_events/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_lumiee_events/static/src/scss/style.scss',
            'theme_lumiee_events/static/src/js/theme.js',
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
