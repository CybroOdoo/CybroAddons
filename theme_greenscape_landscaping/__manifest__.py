# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
{
    'name': 'Theme Greenscape Landscaping',
    'version': '18.0.1.0.0',
    'category': 'Theme/Environment',
    'summary': 'Landscaping, Garden, Environment',
    'description': """
        Theme Greenscape Landscaping provides a modern, responsive design tailored for gardening and landscaping businesses.
        It offers beautiful layouts to showcase services, projects, and testimonials effectively on your Odoo website.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/service_template.xml',
        'views/project_template.xml',
        'data/website_menu_data.xml',
        'views/snippets/s_hero.xml',
        'views/snippets/s_trust.xml',
        'views/snippets/s_about.xml',
        'views/snippets/s_services.xml',
        'views/snippets/s_testimonials.xml',
        'views/snippets/s_process.xml',
        'views/snippets/s_cta.xml',
        'views/snippets/snippets.xml',
        'views/home_template.xml',
        'views/contact_template.xml',
        'views/about_template.xml',
        'views/layout_template.xml',
        'views/project_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_greenscape_landscaping/static/src/scss/style.scss',
            'theme_greenscape_landscaping/static/src/js/main.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
