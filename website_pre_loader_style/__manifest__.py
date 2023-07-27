# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
    'name': 'Website Pre-Loader',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': "Customized pre-loader for websites",
    'description': "This module allows users to customize the pre-loader"
                   "style for the website by selecting a preferred style in"
                   "the configuration settings. The selected style will be "
                   "applied to every loading screen.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_pre_loader_style/static/src/js/payment_processing.js',
        ],
        'web.assets_backend': [
            'website_pre_loader_style/static/src/js/block_ui.js',
            'website_pre_loader_style/static/src/js/website_pre_loader.js',
            'website_pre_loader_style/static/src/xml/*',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'licence': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
