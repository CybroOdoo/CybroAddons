# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
    'name': "Lifeline for Task",
    'summary': """Lifeline Progressbar for Tasks (100% -> 0%)""",
    'description': """Calculates the time remaining based on live time & deadline.""",
    'author': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'category': 'Project',
    'version': '9.0.1.0.0',
    'depends': ['base', 'project'],
    'data': [
        'views/task_lifeline_view.xml',
        'views/progress_bar_view.xml',
        'views/progress_bar_settings.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
