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
    'version': '19.0.1.0.0',
    'summary': 'Custom Odoo Website Theme — OdoNova brand identity.',
    'description': """
        A production-ready website theme for OdoNova.
    """,
    'category': 'Theme/Creative',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': [
        'website',
    ],

    'data': [
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/login_templates.xml',
        'views/contactus_templates.xml',
        'views/contactus_thank_you.xml',
        'views/industries_templates.xml',
        'views/case_studies_templates.xml',
        'views/about_templates.xml',
        'views/snippets/snippets.xml',
        'views/snippets/snippets_options.xml',
    ],

    'assets': {
        'web.assets_frontend': [
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
            'theme_odonova/static/src/js/theme.js',
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
