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
{
    'name': 'Theme Aquere',
    'version': '20.0.1.0.0',
    'category': 'Theme',
    'summary': 'A calm blue website theme for a premium packaged drinking '
               'water brand: story, water range, process, planet and contact.',
    'description': 'Theme Aquere gives a premium water brand a complete '
                   'website: a floating glass header pill, a cinematic hero, '
                   'bento story tiles, a scroll-lit philosophy statement, an '
                   'interactive collection showcase, a sticky process '
                   'tracker, testimonials, an enquiry form and an oversized '
                   'wordmark footer. Every page is made of editable '
                   'sections that can be dropped from the website builder.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_crm', 'website_mass_mailing'],
    'data': [
        'views/snippets/s_aquere_blocks.xml',
        'views/snippets/snippets.xml',
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/story_templates.xml',
        'views/water_templates.xml',
        'views/process_templates.xml',
        'views/planet_templates.xml',
        'views/contact_templates.xml',
        'data/website_menu_data.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_aquere/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_aquere/static/src/css/fonts.css',
            'theme_aquere/static/src/css/icons.css',
            'theme_aquere/static/src/css/aquere.css',
            'theme_aquere/static/src/scss/odoo_overrides.scss',
            'theme_aquere/static/src/scss/header.scss',
            'theme_aquere/static/src/interactions/*.js',
        ],
        'website.assets_inside_builder_iframe': [
            'theme_aquere/static/src/scss/edit_mode.edit.scss',
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
