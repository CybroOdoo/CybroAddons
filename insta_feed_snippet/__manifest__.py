# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Instagram Feed Snippet',
    'version': '16.0.0.0.0',
    'summary': 'Instagram Feed Snippet',
    'description': """The Odoo Instagram Feed Snippet module provides a feature to add an Instagram feed in Odoo.""",
    'category': 'Website',
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': ['base', 'product', 'website', 'website_sale', 'sale'],
    'data': ['security/ir.model.access.csv',
             'views/insta_post.xml',
             'views/insta_profile.xml',
             'views/snippet_structure_inherit.xml',
             'views/website.xml'
             ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_frontend': [
            '/insta_feed_snippet/static/src/image/carousel.jpg',
            'insta_feed_snippet/static/src/js/caroursel.js',
        ],
    },
}
