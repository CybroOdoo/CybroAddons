# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Quality Assurance',
    'version': '18.0.1.0.0',
    'summary': 'Manage Our Quality Assurance Processes in Odoo 18 Community',
    'description': """
    This module provides features to manage basic quality assurance procedures.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Inventory',
    'depends': ['product', 'stock', 'purchase_stock'],
    'data': [
        'data/quality_alert_sequence.xml',
        'security/quality_assurance_security.xml',
        'views/quality_measure_views.xml',
        'security/ir.model.access.csv',
        'views/quality_alert_views.xml',
        'views/quality_test_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
