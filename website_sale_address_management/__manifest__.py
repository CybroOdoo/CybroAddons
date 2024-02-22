# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
{
    'name': "Website Sale Address Management",
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """This module helps you to show or hide fields by switching 
    on/off toggles,set fields as mandatory or not and  set default country.""",
    'description': """This module helps you to show or hide fields by switching
    on/off toggles.You can set fields as mandatory or not and also set default
    country.All of these features can be changed from configuration settings 
    of Website  module.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'website_sale_address_management/static/src/css/'
            'address_management.css',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
