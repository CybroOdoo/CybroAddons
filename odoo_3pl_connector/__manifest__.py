# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
    'name': "Odoo 3pl Connector",
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': """Facilitates seamless integration  between Odoo and 3pl 
     for efficient supply chain management.""",
    'description': """Enabling a smooth integration between Odoo and 3pl 
     streamlines supply chain management for enhanced efficiency. This 
     integration facilitates seamless coordination, optimizing processes 
     across the entire supply chain. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/ftp_server_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
        'wizard/tpl_operation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_3pl_connector/static/src/js/action_manager.js',
        ],
    },
    'external_dependencies': {
        'python': ['openpyxl']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
