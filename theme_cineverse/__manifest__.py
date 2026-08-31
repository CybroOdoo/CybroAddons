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
    'name': 'CineVerse Theme',
    'version': '19.0.1.0.0',
    'category': 'Theme/Entertainment',
    'summary': 'Premium Cinema & Entertainment Odoo Theme',
    'description': 'Premium Cinema & Entertainment Odoo Theme with immersive animations, 3D tickets, and cinematic galleries.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'data/cineverse_movie_data.xml',
        'views/cineverse_movie_views.xml',
        'views/layout.xml',
        'views/home_templates.xml',
        'views/movies_templates.xml',
        'views/showtimes_templates.xml',
        'views/vip_templates.xml',
        'views/gallery_templates.xml',
        'views/contact_templates.xml',
        'data/website_menu_data.xml',
        'views/snippets/snippet_groups.xml',
        'views/snippets/s_cineverse_hero.xml',
        'views/snippets/s_cineverse_experience.xml',
        'views/snippets/s_cineverse_movies_teaser.xml',
        'views/snippets/s_cineverse_testimonials.xml',
        'views/snippets/s_cineverse_page_hero.xml',
        'views/snippets/s_cineverse_film_strip.xml',
        'views/snippets/s_cineverse_upcoming_grid.xml',
        'views/snippets/s_cineverse_showtimes_board.xml',
        'views/snippets/s_cineverse_vip_showcase.xml',
        'views/snippets/s_cineverse_vip_benefits.xml',
        'views/snippets/s_cineverse_vip_events.xml',
        'views/snippets/s_cineverse_gallery_tape.xml',
        'views/snippets/s_cineverse_contact_form.xml',
        'views/snippets/s_cineverse_transport.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_cineverse/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_cineverse/static/src/scss/style.scss',
            'theme_cineverse/static/src/js/script.js',
        ],
    },
    'images': [
    	'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
        'static/description/icon.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
