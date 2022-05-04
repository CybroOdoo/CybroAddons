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
    'name': "Odoo Support Request",
    'category': 'Productivity',
    'summary': 'Create Odoo Support Request To Cybrosys',
    'version': '14.0.1.0.1',
    'description': """Odoo Support""",
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': ['base'],
    'qweb': ['static/src/xml/systray_theme.xml'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/wizards.xml',
        'views/assets.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],

}
