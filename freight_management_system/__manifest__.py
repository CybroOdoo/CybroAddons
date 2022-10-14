# -*- coding: utf-8 -*-
###################################################################################
#    Freight Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Freight Management',
    'version': '16.0.1.0.0',
    'summary': 'Module for Managing All Frieght Operations',
    'description': 'Module for Managing All Frieght Operations',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product', 'account'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/freight_order_data.xml',
        'views/freight_order.xml',
        'views/freight_port.xml',
        'views/freight_container.xml',
        'views/custom_clearance.xml',
        'views/order_track.xml',
        'report/report_order.xml',
        'report/report_tracking.xml',
        'wizard/custom_revision.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
