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
    'name': 'Theme VoyageX',
    'version': '19.0.1.0.0',
    'category': 'Theme/Creative',
    'summary': 'Premium Travel Planner - Mobile App Showcase Theme',
    'description': """
        VoyageX Theme for Odoo 19
        =========================
        A modern, premium mobile app showcase theme designed for travel
        and SaaS product landing pages. Features phone mockup displays,
        gradient CTAs, app gallery sections, and responsive layouts.

        Key Features:
        - Hero section with 3-phone mockup display
        - Feature sections with phone device frames
        - App gallery with hover animations
        - Gradient CTA sections with store buttons
        - Screen showcase cards with 3D hover effects
        - QR code download section
        - Fully responsive design
    """,
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/layout/templates.xml',
        'data/pages/home_page.xml',
        'views/snippets/snippet_groups.xml',
        'views/snippets/s_vx_hero.xml',
        'views/snippets/s_vx_featured.xml',
        'views/snippets/s_vx_feature_left.xml',
        'views/snippets/s_vx_feature_right.xml',
        'views/snippets/s_vx_collab_visual.xml',
        'views/snippets/s_vx_gallery.xml',
        'views/snippets/s_vx_cta.xml',
        'views/snippets/s_vx_feature_hero.xml',
        'views/snippets/s_vx_more_features.xml',
        'views/snippets/s_vx_screen_showcase.xml',
        'views/snippets/s_vx_screen_showcase_alt.xml',
        'views/snippets/s_vx_getapp_hero.xml',
        'views/snippets/s_vx_qr_download.xml',
        'views/snippets/s_vx_requirements.xml',
        'data/menu.xml',
        'data/pages/features_page.xml',
        'data/pages/screens_page.xml',
        'data/pages/getapp_page.xml',
        'data/pages/design_system_page.xml',
        'data/pages/login_signup_page.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'theme_voyagex/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_frontend': [
            'theme_voyagex/static/src/scss/theme.scss',
            'theme_voyagex/static/src/js/theme.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
