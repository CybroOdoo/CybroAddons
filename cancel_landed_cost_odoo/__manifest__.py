# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    'name': "Cancel Landed Cost",
    'version': "16.0.1.0.0",
    'category': 'Purchases,Accounting,Warehouse',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'summary': 'This module helps to cancel landed costs',
    'description': 'This module helps to cancel Landed Costs and allows you '
                   'to cancel multiple Landed Costs from the tree view. There '
                   'are three ways in which you can cancel the Landed Costs'
                   'Cancel Only, Cancel and Reset to Draft,Cancel and Delete',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['account', 'purchase', 'stock_landed_costs'],
    'data': [
        'security/cancel_landed_cost_odoo_groups.xml',
        'data/stock_landed_cost_data.xml',
        'views/stock_landed_cost_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
