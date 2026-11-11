# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
    'name': 'Dynamic Hover on Related Fields',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Dynamic Hover on Related Fields helps you to '
               'show the configured fields in a tooltip popup.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': [
        'security/ir.access.csv',
        'views/hover_related_fields_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_hover_on_related_fields/static/src/xml/tooltip.xml',
            'dynamic_hover_on_related_fields/static/src/xml/relatedFieldTooltip.xml',
            'dynamic_hover_on_related_fields/static/src/xml/many2oneField.xml',
            'dynamic_hover_on_related_fields/static/src/xml/listRenderer.xml',
            'dynamic_hover_on_related_fields/static/src/xml/tagsList.xml',
            'dynamic_hover_on_related_fields/static/src/xml/webFieldTooltip.xml',
            'dynamic_hover_on_related_fields/static/src/js/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
