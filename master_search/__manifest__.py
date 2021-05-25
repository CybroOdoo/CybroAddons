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
    'name': 'Master Search',
    'version': '13.0.1.0.0',
    'summary': """Helps to search the records of the objects""",
    'description': """This module helps users search the records of the objects for all the 
                    master search group enabled users.""",
    'category': 'settings',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/master_search_view.xml',
        'views/template.xml',
    ],
    'installable': True,
    'auto_install': False,
}
