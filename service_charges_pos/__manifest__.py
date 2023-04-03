# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
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
    'name': 'POS Service Charges',
    'version': '16.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': 'Allows you to set service charges.',
    'description': 'Allows you to set service charges for an order by globally and session wise.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_config_settings.xml',
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'service_charges_pos/static/src/js/pos_load_data.js',
            'service_charges_pos/static/src/js/service_charge_button.js',
            'service_charges_pos/static/src/xml/ServiceChargeButton.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,

}
