# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'POS Paid Order Delete',
    'version': '18.0.1.0.0',
    'category': 'POS',
    'summary': "Can Delete POS Orders in Paid State With or Without Code",
    'description': "This app allow the specified user to delete the pos orders"
                   " with or without code in paid state by unlinking the "
                   "payments of corresponding order.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data':
        [
        'security/ir.model.access.csv',
        'security/pos_order_delete_groups.xml',
        'data/pos_order_data.xml',
        'views/res_config_settings_views.xml',
        'wizard/delete_paid_pos_order_views.xml'
        ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'uninstall_hook': '_uninstall_hook',
}

