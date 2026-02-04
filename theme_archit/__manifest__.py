# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    'name': 'Theme Archit',
    'version': '18.0.1.0.0',
    'category': 'Theme',
    'summary': 'Design The Web Pages with theme Archit',
    'description': 'Theme Archit is a specialized web design module for Odoo, '
                   'providing a range of tools and '
                   'features to streamline the process of designing and '
                   'developing websites within the Odoo platform.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': [
        'views/footer.xml',
        'views/header.xml',
        'views/loging_templates.xml',
        'views/contacts_templates.xml',
        'views/snippets/error.xml',
        'views/snippets/about.xml',
        'views/snippets/about_banner.xml',
        'views/snippets/about_partner.xml',
        'views/snippets/about_job_form.xml',
        'views/snippets/blank.xml',
        'views/snippets/blog.xml',
        'views/snippets/blog_banner.xml',
        'views/snippets/contact.xml',
        'views/snippets/contact_banner.xml',
        'views/snippets/index.xml',
        'views/snippets/index_banner.xml',
        'views/snippets/index_about.xml',
        'views/snippets/projects.xml',
        'views/snippets/recognition.xml',
        'views/snippets/single_blog.xml',
        'views/snippets/single_project.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_archit/static/src/js/index.js',
            'theme_archit/static/src/js/contact.js',
            'theme_archit/static/src/js/owl.carousel.min.js',
            'theme_archit/static/src/css/animate.min.css',
            'theme_archit/static/src/css/owl.carousel.min.css',
            'theme_archit/static/src/css/owl.theme.default.min.css',
            'theme_archit/static/src/css/style.css',
            'theme_archit/static/src/css/buy_now_fix.css',
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
