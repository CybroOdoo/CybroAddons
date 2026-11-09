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
    'name': 'Merge RFQ',
    'version': '20.0.1.0.0',
    'category': 'Purchases',
    'summary': """Merge two or more RFQs into one purchase order, Odoo 20 Merge RFQ, Purchase RFQ Merge""",
    'description': """Merge RFQ for Odoo 20 lets users merge multiple Requests
    for Quotation (RFQs) into a new or an existing RFQ, and cancel or delete
    the other RFQs. Only RFQs in the RFQ or RFQ Sent state can be merged.""",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase'],
    'data': [
        'security/ir.access.csv',
        'wizard/merge_rfq_wizard.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
