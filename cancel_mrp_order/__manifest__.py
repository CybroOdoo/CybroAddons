# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Cancel Manufacturing Order',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Cancel done manufacturing orders from the form or the list view',
    'description': 'Allows users to cancel done manufacturing orders by '
                   'clicking the "Cancel" button. Multiple manufacturing '
                   'orders can also be cancelled from the list view by '
                   'choosing "Cancel Manufacturing Order" from the Action menu.',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mrp', 'stock'],
    'data': [
        'security/cancel_mrp_order_groups.xml',
        'views/mrp_production_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
