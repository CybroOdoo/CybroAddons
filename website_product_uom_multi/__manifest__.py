# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    'name': 'Website Product Multi Uom',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Select the Products UOM before adding to Cart',
    'description': 'This module allows customers to select the preferred '
                   'Unit of Measure (UOM) for products directly from the '
                   'website before adding them to the cart. It provides a '
                   'dropdown button for changing the UOM, similar to the '
                   'pricelist dropdown, ensuring that the product price '
                   'updates accordingly based on the selected UOM. This '
                   'customization enhances the shopping experience by giving '
                   'customers the flexibility to choose product quantities '
                   'that best suit their needs.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'uom', 'website_sale_product_configurator'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "/website_product_uom_multi/static/src/js/uom_button.js",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
