# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Muflih c(odoo@cybrosys.com)
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
    'name': 'Media Repository',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Centralized location for storing, organizing, searching, and managing media assets',
    'description': 'The Media Repository module provides a centralized platform for storing, organizing, '
                   'and managing media assets within Odoo. Users can upload files, categorize them, search efficiently.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/media_repository_groups.xml',
        'security/ir.model.access.csv',
        'security/media_repository_record_rules.xml',
        'data/ir_config_parameter_data.xml',
        'views/media_asset_views.xml',
        'views/media_category_views.xml',
        'views/media_type_dashboard_views.xml',
        'views/media_tag_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'media_repository/static/src/js/dashboard.js',
            'media_repository/static/src/xml/dashboard.xml',
            'media_repository/static/src/js/large_file_binary_field.js',
            'media_repository/static/src/xml/large_file_binary_field.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}