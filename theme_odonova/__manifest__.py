# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Theme OdoNova',
    'version': '18.0.1.0.0',
    'summary': 'Custom Odoo Website Theme — OdoNova brand identity.',
    'description': """
        A production-ready website theme for OdoNova.
    """,
    'category': 'Theme/Creative',
    'author': 'Cyrbosys',
    'depends': ['website'],
    'data': [
        # 1. Asset bundles (CSS/JS injection)
        'views/assets.xml',
        # 2. QWeb template overrides (header, footer, homepage layout)
        'views/layout_templates.xml',
        'views/home_templates.xml',
        # 3. Custom Login Page
        'views/login_templates.xml',
        # 4. Custom Consultation / Contact Us Page
        'views/contactus_templates.xml',
        'views/contactus_thank_you.xml',
        # 5. Industries, Case Studies, and About Pages
        'views/industries_templates.xml',
        'views/case_studies_templates.xml',
        'views/about_templates.xml',
        # 6. Website configuration record — sets this as the active theme
        'data/website_config.xml',
        # 4. Snippets
        'views/snippets/snippets.xml',
        'views/snippets/snippets_options.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            # SCSS — order is critical: variables first, then base, then components
            'theme_odonova/static/src/scss/variables.scss',
            'theme_odonova/static/src/scss/bootstrap_overrides.scss',
            'theme_odonova/static/src/scss/base.scss',
            'theme_odonova/static/src/scss/header.scss',
            'theme_odonova/static/src/scss/hero.scss',
            'theme_odonova/static/src/scss/services.scss',
            'theme_odonova/static/src/scss/modules_grid.scss',
            'theme_odonova/static/src/scss/cta.scss',
            'theme_odonova/static/src/scss/footer.scss',
            'theme_odonova/static/src/scss/about.scss',
            'theme_odonova/static/src/scss/industries.scss',
            'theme_odonova/static/src/scss/case_studies.scss',
            'theme_odonova/static/src/scss/consultation.scss',
            'theme_odonova/static/src/scss/login.scss',
            'theme_odonova/static/src/scss/animations.scss',
            'theme_odonova/static/src/scss/responsive.scss',
            # JS
            'theme_odonova/static/src/js/theme.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'images_preview_theme': {
        'website.s_cover_default_image': '/theme_odonova/static/description/images/banner.jpg',
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
