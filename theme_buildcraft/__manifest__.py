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
    'version': '17.0.1.0.0',
    'category': 'Theme/Construction',
    'summary': 'Premium Construction & Real Estate Website Theme',
    'description': """
        BuildCraft is a construction company theme for the Odoo 17 website.
        It brings home, about, services, projects, team, blog and contact
        pages, building blocks for the website editor, and a Projects menu
        to publish the projects of the company.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_blog', 'website_crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/buildcraft_project_security.xml',
        'views/snippets/s_buildcraft_hero.xml',
        'views/snippets/s_buildcraft_about.xml',
        'views/snippets/s_buildcraft_services.xml',
        'views/snippets/s_buildcraft_projects.xml',
        'views/snippets/s_buildcraft_process.xml',
        'views/snippets/s_buildcraft_cta.xml',
        'views/snippets/s_buildcraft_team.xml',
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
            'theme_buildcraft/static/src/css/style.css',
            'theme_buildcraft/static/src/js/theme.js',
        ],
        'web.assets_tests': [
            'theme_buildcraft/static/tests/tours/theme_buildcraft_tour.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'uninstall_hook': '_theme_buildcraft_uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
