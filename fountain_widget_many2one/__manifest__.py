# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "Fountain Widget",
    "version": "16.0.1.0.0",
    "category": 'Extra Tools',
    "summary": "This widget is used to select the many2one field in fountain "
               "manner.",
    "description": "This is a widget for many2one fields. By using this "
                   "widget we can select record in a fountain manner. It "
                   "generates dynamic dropdown menus with hierarchical options "
                   "and thus Supports parent-child relationships between "
                   "dropdown options.",
    "author": "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ['base'],
    'assets': {
        'web.assets_backend': [
            'fountain_widget_many2one/static/src/js/fountain_widget_many2one.js',
            'fountain_widget_many2one/static/src/xml/fountain_widget_many2one.xml',
            'fountain_widget_many2one/static/src/css/fountain_widget_many2one.css',
            'fountain_widget_many2one/static/src/css/fountain_widget_many2one.scss',
            'fountain_widget_many2one/static/src/xml/fountain_widget_component.xml',
            'fountain_widget_many2one/static/src/js/fountain_widget_component.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
