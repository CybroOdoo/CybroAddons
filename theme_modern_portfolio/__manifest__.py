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
    'name': 'Theme Modern Portfolio',
    'version': '18.0.1.0.0',
    'category': 'Theme/Website',
    'summary': 'Modern Portfolio Theme for Odoo Website',
    'description': 'A modern portfolio theme with hero sections, portfolio grid, stats counter, and contact forms.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'website': 'https://www.cybrosys.com',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_menu_data.xml',
        'views/portfolio_project_views.xml',
        'views/website_templates.xml',
        'views/homepage.xml',
        'views/website_project_detail.xml',
        'views/website_contactus.xml',
        'views/snippets/snippet_groups.xml',
        'views/snippets/snippets_templates.xml',
        'views/snippets/portfolio_hero_templates.xml',
        'views/snippets/portfolio_welcome_templates.xml',
        'views/snippets/portfolio_stats_templates.xml',
        'views/snippets/portfolio_grid_templates.xml',
        'views/snippets/portfolio_about_templates.xml',
        'views/snippets/portfolio_features_templates.xml',
        'views/snippets/portfolio_contact_templates.xml',
        'views/snippets/portfolio_featured_project_template.xml',
        'views/snippets/portfolio_technologies_template.xml',
        'views/snippets/project/project_layout.xml',
        'views/snippets/project/project_feature.xml',
        'views/snippets/project/project_three_column.xml',
        'views/snippets/project/project_two_column.xml',
        'views/snippets/project/project_steps.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Montserrat:wght@400;500;600;700&family=DM+Serif+Display&display=swap',
            '/theme_modern_portfolio/static/src/css/style.css',
            '/theme_modern_portfolio/static/src/js/*.js',
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
