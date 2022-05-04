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
    'name': "To Do List",
    'summary': """
        Create Todo List Using Activities""",
    'description': """
        Scheduling Activities For each model  and General Activities.
            """,
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'live_test_url': 'https://youtu.be/LGiDWPFdkbks',
    'category': 'Tools',
    'version': '14.0.1.0.0',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/recurring.xml',
        'data/general.xml',
        'views/views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
