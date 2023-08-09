# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Highlight Mandatory Field',
    'version': '16.0.1.0.0',
    'summary': 'This Module will help to customize mandatory fields in odoo',
    'description': """User can customize the mandatory field's view by 
                    different colors""",
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'contacts'],
    'data': [
        'views/res_config_settings_views.xml',
        ],
    'assets': {
        'web.assets_backend': [
            'mandatory_field_highlight/static/src/js/action_manager.js',
            'mandatory_field_highlight/static/src/scss/field.scss',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
