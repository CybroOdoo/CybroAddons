# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Amazon Forecast Integration",
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'To predict the stock demand.',
    'description': """
     This module helps to predict the demand and maintain right level of
      inventory.
    """,
    'sequence': 20,
    'author': " Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'support': 'Cybrosys Techno Solutions',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/amazon_dataset_views.xml',
        'views/amazon_fetch_data_views.xml',
        'views/amazon_bucket_views.xml',
        'views/menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js',
            'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js',
            'amazon_forecast_integration/static/src/js/graphView.js',
            'amazon_forecast_integration/static/src/xml/graph_view.xml',
        ]
    },
    'external_dependencies': {'python': ['boto3']},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
