# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Theme The Chef',
    'version': '17.0.1.0.0',
    'category': 'Theme/Creative',
    'summary': 'Theme The Chef is a popular attractive and unique '
               'front end theme for your restaurant website.',
    'description': 'Design Web Pages with Theme The Chef',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_bookings_data.xml',
        'views/website_snippet_templates.xml',
        'views/website_templates.xml',
        'views/website_bookings_views.xml',
        'views/website_bookings_submit_templates.xml',
        'views/snippets/about_templates.xml',
        'views/snippets/banner_templates.xml',
        'views/snippets/branches_templates.xml',
        'views/snippets/happy_templates.xml',
        'views/snippets/menu_templates.xml',
        'views/snippets/reservation_templates.xml',
        'views/snippets/special_templates.xml',
        'views/snippets/special_left_templates.xml',
        'views/snippets/team_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_the_chef/static/src/css/style.css',
            'theme_the_chef/static/src/css/animate.min.css',
            'theme_the_chef/static/src/css/owl.carousel.min.css',
            'theme_the_chef/static/src/css/owl.theme.default.min.css',
            'theme_the_chef/static/src/js/custom.js',
            'theme_the_chef/static/src/js/owl.carousel.js',
            'theme_the_chef/static/src/js/date_selection.js'
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
