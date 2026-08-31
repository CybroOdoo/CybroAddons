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
    'name': 'Theme BuildCraft',
    'version': '19.0.1.0.0',
    'category': 'Theme/Construction',
    'summary': 'Premium Construction & Real Estate Website Theme',
    'description': """
        BuildCraft - Premium Construction Company Theme for Odoo 19
        A professional, modern theme designed for construction companies,
        real estate developers, and architecture firms.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_blog', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/snippets/s_buildcraft_hero.xml',
        'views/snippets/s_buildcraft_about.xml',
        'views/snippets/s_buildcraft_services.xml',
        'views/snippets/s_buildcraft_projects.xml',
        'views/snippets/s_buildcraft_process.xml',
        'views/snippets/s_buildcraft_cta.xml',
        'views/snippets/s_buildcraft_testimonials.xml',
        'views/snippets/s_buildcraft_blog.xml',
        'views/snippets/snippets.xml',
        'views/layout_template.xml',
        'views/homepage_template.xml',
        'views/about_template.xml',
        'views/contact_template.xml',
        'views/blog_template.xml',
        'views/projects_template.xml',
        'views/services_template.xml',
        'views/team_template.xml',
        'views/project_detail_template.xml',
        'views/project_view.xml',
        'data/website_menu_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_buildcraft/static/src/css/style.css',
            '/theme_buildcraft/static/src/js/theme.js',
        ],
        'website.website_builder_assets': [
            '/theme_buildcraft/static/src/js/builder_patches.js',
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
    'uninstall_hook': '_theme_buildcraft_uninstall_hook',
}
