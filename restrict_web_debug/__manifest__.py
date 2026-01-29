# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
    'name': 'Userwise Developer Mode Restriction',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module allows the hiding of the debug option based on'
               ' user-specific settings',
    "description": 'Restrict developer mode for each users with disabling an '
                   '"Show debug icon" user group, then user could not able to '
                   'access debug mode.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'data': [
        'security/restrict_web_debug_groups.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'restrict_web_debug/static/src/js/DebugMenuBasic.js',
        ],
        'web.assets_qweb': [
            'restrict_web_debug/static/src/xml/restrict_debug_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install ': False,
    'application': False,
}
