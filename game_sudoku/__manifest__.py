# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
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
    'name': 'Odoo Games - Sudoku',
    'version': '10.0.1.0.0',
    'summary': """Sudoku Game.""",
    'description': """We can play SUDOKU.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': '',
    'depends': ['base', 'hr'],
    'license': 'LGPL-3',
    'data': [
        'security/security_data.xml',
        'security/ir.model.access.csv',
        'views/game_approve_sequence.xml',
        'views/game_template.xml',
        'views/main_menu.xml',
        'views/sudoku_menu.xml',
    ],
    'demo': [],
    'qweb': [
        "static/src/xml/sudoku.xml",
        "static/src/xml/game.xml",
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
