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
    'name': 'Odoo ExcaliDraw',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Embeds Excalidraw in Odoo',
    'description': """This module Embeds Excalidraw in Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mrp', 'project', 'web_editor'],
    'data': [
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_excalidraw/static/lib/react/react.production.min.js',
            'odoo_excalidraw/static/lib/react/react-dom.production.min.js',
            'odoo_excalidraw/static/lib/excalidraw/excalidraw.production.min.js',
            'odoo_excalidraw/static/src/css/excalidraw.css',
            'odoo_excalidraw/static/src/js/excalidraw_client_action.js',
            'odoo_excalidraw/static/src/xml/excalidraw_client_action.xml',
            'odoo_excalidraw/static/src/js/excalidraw_dialog.js',
            'odoo_excalidraw/static/src/xml/excalidraw_dialog.xml',
        ],
        'web_editor.backend_assets_wysiwyg': [
            'odoo_excalidraw/static/src/js/html_field_patch.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
