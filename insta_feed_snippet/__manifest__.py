# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Henna Mehjabin(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL-3 v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL-3 v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL-3 v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Instagram Feed Snippet',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Instagram Feed Snippet',
    'description': """The Odoo Instagram Feed Snippet module provides
    a feature to add an Instagram feed in Odoo.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'website_sale'],
    'data': ['security/ir.model.access.csv',
             'views/insta_post_views.xml',
             'views/insta_profile_views.xml',
             'views/snippet_structure_inherit.xml',
             ],
    'assets': {
        'web.assets_frontend': [
            'insta_feed_snippet/static/src/image/insta.png',
            'insta_feed_snippet/static/src/xml/carousel_template.xml',
            'insta_feed_snippet/static/src/js/caroursel.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
