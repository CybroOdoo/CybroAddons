# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Theme Archit',
    'summary': 'Design The Web Pages with theme Archit',
    'description': 'Theme Archit Is A Ultimate Theme for Your Odoo 15.'
               'This Theme Will Give You A New Experience With Odoo',
    'category': 'Theme/eCommerce',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': [
        'views/layout_templates.xml',
        'views/footer_templates.xml',
        'views/header_templates.xml',
        'views/snippets/error_templates.xml',
        'views/snippets/about_banner_templates.xml',
        'views/snippets/about_partner_templates.xml',
        'views/snippets/about_job_form_templates.xml',
        'views/snippets/blank_templates.xml',
        'views/snippets/blog_templates.xml',
        'views/snippets/blog_banner_templates.xml',
        'views/snippets/contact_templates.xml',
        'views/snippets/contact_banner_templates.xml',
        'views/snippets/index_templates.xml',
        'views/snippets/index_banner_templates.xml',
        'views/snippets/index_about_templates.xml',
        'views/snippets/login_templates_templates.xml',
        'views/snippets/projects_templates.xml',
        'views/snippets/recognition_templates.xml',
        'views/snippets/register_templates.xml',
        'views/snippets/single_blog_templates.xml',
        'views/snippets/single_project_templates.xml',
        'views/snippets/about_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_archit/static/src/css/owl.carousel.min.css',
            '/theme_archit/static/src/css/owl.theme.default.min.css',
            '/theme_archit/static/src/css/style.css',
            '/theme_archit/static/src/js/owl.carousel.min.js',
            '/theme_archit/static/src/js/index.js',
            '/theme_archit/static/src/js/contact.js'
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
