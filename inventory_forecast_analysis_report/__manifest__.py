# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raveena V (odoo@cybrosys.com)
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
#############################################################################
{
    "name": "Inventory Forecast Analysis Report",
    "version": "16.0.1.0.1",
    "category": "Warehouse",
    "summary": "Helps to find all the stock quantities",
    "description": "This module allows the user to find all the "
    "stock quantities like onhand, sold, forecasted,"
    " pending, minimum and suggested for all the products.",
    "author": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["stock", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/forecast_report_views.xml",
        "views/product_template_views.xml",
        "wizards/forecast_analysis_report_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
