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
    "name": "POS Invoice Register Payment",
    "version": "20.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Create payments and register invoice payments from the POS",
    "description": "Create payments for customers and register payments for their invoices from the Point of Sale.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_invoice_payment/static/src/js/pos_partnerline.js",
            "pos_invoice_payment/static/src/js/invoicing_button.js",
            "pos_invoice_payment/static/src/js/payment_popup.js",
            "pos_invoice_payment/static/src/js/invoicing_screen.js",
            "pos_invoice_payment/static/src/xml/partnerline_button_templates.xml",
            "pos_invoice_payment/static/src/xml/payment_pop_templates.xml",
            "pos_invoice_payment/static/src/xml/numpad_invoicing_button_templates.xml",
            "pos_invoice_payment/static/src/xml/invoice_screen_templates.xml",
            "pos_invoice_payment/static/src/css/invoice_list.scss",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    'auto_install': False,
    'application': False,
}
