# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
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
    'name': 'Parent Team & Targets',
    'version': '9.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sales Team Targets and Parent Teams',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'depends': ['crm', 'sale'],
    'images': ['static/description/banner.jpg'],
    'website': 'http://www.cybrosys.com',
    'data': [
        'views/parent_team.xml',
        'views/sales_man_target.xml',
        'views/sales_team_target.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}