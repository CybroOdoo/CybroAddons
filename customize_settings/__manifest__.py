# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': "Odoo Debranding V16",
    'version': "16.0.1.0.0",
    'summary': """Odoo Backend and Frontend Debranding In V16""",
    'description': """Odoo Debrand, Odooo Debranding, Debrand, Debranding, Backend Debrand, Frontend Debranding, Odoo Backend and Frontend Debranding""",
    'live_test_url': 'https://www.youtube.com/watch?v=fYSPARjmYA4',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'category': 'Tools',
    'depends': ['website', 'base_setup', 'base', 'web'],
    'data': [
        'views/ir_module_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'customize_settings/static/src/js/web_client.js',
            'customize_settings/static/src/xml/user_menu_items.xml',
            'customize_settings/static/src/js/error_dialogs.js',
            'customize_settings/static/src/js/dialogs.js'
        ],
        'web.assets_frontend': [
        ]
    },
    'qweb': ["static/src/xml/base.xml"],
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': '_pre_init_odoo_bot',
    'uninstall_hook': 'uninstall_hook_odoo_bot',
}
