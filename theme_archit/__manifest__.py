# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Archit',
    'description': 'Design The Web Pages with theme Archit',
    'summary': 'Design The Web Pages with theme Archit',
    'category': 'Theme/Corporate',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': [
        'views/assets.xml',
        'views/layout.xml',
        'views/footer.xml',
        'views/header.xml',
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
        'views/snippets/login.xml',
        'views/snippets/projects.xml',
        'views/snippets/recognition.xml',
        'views/snippets/register.xml',
        'views/snippets/single_blog.xml',
        'views/snippets/single_project.xml'

    ],
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
