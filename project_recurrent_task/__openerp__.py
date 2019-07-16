# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Recurrent Task In Project',
    'version': '9.0.1.0.0',
    'summary': """Create Recurrent Task in Project""",
    'description': 'This module helps you to create recurrent task in project',
    'category': 'Project Management',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'project', 'subscription'],
    'data': [
        'demo/demo_data.xml',
        'views/recurrent_task_view.xml',
        'views/approve_recurrent_task_view.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
