# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Instant Import',
    'version': '18.0.1.0.0',
    'depends': ['base', 'web', 'base_import'],
    'category': 'Tools',
    'summary': 'Module for fast bulk imports using PostgreSQL COPY',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'application': True,
    'sequence': -333,
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'instant_import/static/src/js/import_component.js',
            'instant_import/static/src/js/import_component.xml',
            'instant_import/static/src/js/instant_import.js',
            'instant_import/static/src/js/templates.xml',
        ],
    },
    'external_dependencies': {
        'python': ['pandas'],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'post_init_hook': 'setup_db_level_functions',
    'uninstall_hook': 'delete_contact',
}
