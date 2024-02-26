# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': '17.0.1.0.0',
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
        'views/snippets/login.xml',
        'views/snippets/projects.xml',
        'views/snippets/recognition.xml',
        'views/snippets/register.xml',
        'views/snippets/single_blog.xml',
        'views/snippets/single_project.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_archit/static/src/js/owl.carousel.js',
            '/theme_archit/static/src/js/owl.carousel.min.js',
            '/theme_archit/static/src/js/index.js',
            '/theme_archit/static/src/js/contact.js',
            '/theme_archit/static/src/css/animate.min.css',
            '/theme_archit/static/src/css/owl.carousel.min.css',
            '/theme_archit/static/src/css/owl.theme.default.min.css',
            '/theme_archit/static/src/css/style.css',
            'https://fonts.googleapis.com/css2?family=Poppins&amp;family=Space+Mono:ital,wght@0,400;0,700;1,400&amp;family=Work+Sans&amp;display=swap',
            'https://fonts.googleapis.com/css2?family=Overpass+Mono:wght@700&amp;display=swap',
            'https://fonts.googleapis.com/css2?family=Julius+Sans+One&amp;display=swap',
            'https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css',
            'https://fonts.googleapis.com/icon?family=Material+Icons',
            'https://use.fontawesome.com/releases/v5.7.0/css/all.css',
            'https://use.fontawesome.com/releases/v5.7.0/css/all.css',
            'https://fonts.googleapis.com/icon?family=Material+Icons',
            'https://code.jquery.com/jquery-3.5.1.slim.min.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js',
            'https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js',
            'https://maps.googleapis.com/maps/api/js?v=3&amp;sensor=false',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_archit_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
