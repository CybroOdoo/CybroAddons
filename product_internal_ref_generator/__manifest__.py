# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "Product Internal Reference Generator",
    "version": "17.0.1.0.0",
    "category": "Warehouse",
    "summary": "In this Module we can generate internal references",
    "description": """Generating internal reference for the products based 
     on the product details""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["sale_management"],
    "data": [
        'data/ir_sequence_data.xml',
        'data/ir_actions_server_data.xml',
        'views/res_config_settings_views.xml',
    ],
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
