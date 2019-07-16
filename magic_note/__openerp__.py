# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2008-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
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
    'name': "Magic Color Note",
    'summary': """
        Automatically Change the Colour Based on the Date Interval Config of Notes""",
    'description': """
        Set a date interval in integers.
        All notes belonging to the period will be assigned the defined colour
    """,
    'version': '0.2',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Tools',
    'depends': ['base', 'note'],
    'data': ['views/color_note.xml',
             'views/color_config.xml'],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
