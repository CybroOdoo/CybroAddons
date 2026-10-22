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
    "name": "Export Product Images",
    "version": "20.0.1.0.0",
    "category": "Warehouse",
    "summary": """To export product details along with the product images.""",
    "description": "The allowed users can download the product details "
    "along with the product images.",
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "depends": ["product", "web"],
    "external_dependencies": {
        "python": ["xlsxwriter", "Pillow"],
    },
    "data": [
        "security/product_export_with_images_groups.xml",
        "security/ir.access.csv",
        "data/product_export_with_images_data.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
