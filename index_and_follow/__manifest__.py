# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
    'name': 'Website Index and Follow',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """Website Index and Follow Application for Odoo 17""",
    'description': """The module helps you to specify product-level indexing.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/portal_views.xml',
        'views/website_sale_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'index_and_follow/static/src/js/index_and_follow.js', ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False
}
