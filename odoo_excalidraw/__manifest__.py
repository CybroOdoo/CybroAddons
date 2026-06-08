# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Odoo Excalidraw',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Integrates Excalidraw whiteboard into Odoo',
    'description': """
                Embed Excalidraw directly into Odoo to create and manage diagrams, sketches,
                flowcharts, and collaborative visual notes within your business workflows.
                Provides an interactive whiteboard experience for better visualization,
                planning, and team collaboration inside Odoo.
    """,
    'depends': ['base', 'mrp'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'data': [
        'security/ir.model.access.csv',
        'wizard/excalidraw_attach_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_excalidraw/static/lib/react/react.production.min.js',
            'odoo_excalidraw/static/lib/react/react-dom.production.min.js',
            'odoo_excalidraw/static/lib/excalidraw/excalidraw.production.min.js',
            'odoo_excalidraw/static/src/js/excalidraw_client_action.js',
            'odoo_excalidraw/static/src/xml/excalidraw_client_action.xml',
            'odoo_excalidraw/static/src/js/excalidraw_dialog.js',
            'odoo_excalidraw/static/src/xml/excalidraw_dialog.xml',
            'odoo_excalidraw/static/src/js/excalidraw_plugin.js',
            'odoo_excalidraw/static/src/js/html_field_patch.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'auto_install': False,
}
