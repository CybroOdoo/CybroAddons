# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme The Chef',
    'description': 'Theme The Chef is a popular attractive and unique front'
                   ' end theme for your restaurant website.',
    'summary': 'Theme The Chef',
    'category': 'Theme/Creative',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_bookings_data.xml',
        'views/website_snippet.xml',
        'views/layout.xml',
        'views/templates.xml',
        'views/website_bookings.xml',
        'views/website_bookings_submit.xml',
        'views/snippets/about.xml',
        'views/snippets/banner.xml',
        'views/snippets/branches.xml',
        'views/snippets/happy.xml',
        'views/snippets/menu.xml',
        'views/snippets/reservation.xml',
        'views/snippets/special.xml',
        'views/snippets/special_left.xml',
        'views/snippets/team.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_the_chef/static/src/css/style.css',
            'theme_the_chef/static/src/css/animate.min.css',
            'theme_the_chef/static/src/css/owl.carousel.min.css',
            'theme_the_chef/static/src/css/owl.theme.default.min.css',
            'theme_the_chef/static/src/js/custom.js',
            'theme_the_chef/static/src/js/owl.caromodusel.js',
            'theme_the_chef/static/src/js/date_selection.js'
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
