# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Menu Draggable",
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Rearrange the position of menus in each module 
                accordingly""",
    'description': 'Change position of Menus in each module',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'depends': ['base'],
    'data': ['security/ir.model.access.csv'],
    'assets': {
        'web.assets_backend': [
            '/menu_draggable/static/src/js/draggable_menu.js'
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
