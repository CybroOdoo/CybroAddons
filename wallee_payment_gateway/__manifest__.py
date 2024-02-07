# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ansil pv (odoo@cybrosys.com)
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
###############################################################################
{
    "name": "Wallee Payment Gateway",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "summary": "Accept Payments with Wallee on Odoo Website",
    "description": "This module integrates Wallee payment gateway "
    "with Odoo, allowing customers to securely make payments "
    "using Wallee on your website.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["base", "payment", "account", "website_sale"],
    "data": [
        "views/payment_provider_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_provider_data.xml",
    ],
    "external_dependencies": {
        "python": ["wallee"],
    },
    "images": ["static/description/banner.jpg"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
