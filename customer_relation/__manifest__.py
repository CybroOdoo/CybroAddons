# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM (<odoo@cybrosys.com>)
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
    'name': 'Partner Relationship Management',
    'version': '18.0.1.0.0',
    'summary': 'Manages customizable relationships between contacts (e.g., Family, Colleague, Vendor).',
    'description': '''
        Detailed management of relationships between partners (contacts).
        Features include:
        - Defining custom relationship types (e.g., Father, Son).
        - Manually defining reciprocal relationship types.
        - Automatic creation, update, and deletion of reciprocal records for data integrity.
    ''',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'data/relation_type_data.xml',
        'security/ir.model.access.csv',
        'views/relation_type_catogory_views.xml',
        'views/relation_type_views.xml',
        'views/res_partner_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
