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
    "name": "Automated Credit/Debit Note Generation from Return Picking",
    "version": "20.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Generate credit notes and debit notes when returning delivered or received goods",
    "description": "Return done delivery orders and receipts through a wizard that creates the return picking and the matching credit note or debit note.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["sale_stock", "purchase_stock"],
    "data": [
        "security/ir.access.csv",
        "views/stock_picking_views.xml",
        "wizard/return_move_views.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
