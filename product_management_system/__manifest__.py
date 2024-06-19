# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'Product Management System',
    'version': '16.0.1.0.0',
    'category': 'Warehouse , Extra Tools',
    'summary': """This module helps in product management system.""",
    'description': """ Mass actions are operations that might be proceeded for 
    a number of product templates in batch. The tool offers multiple default 
    actions, among which you can select the required ones.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'website_sale', 'purchase', 'stock'],
    'data': [
        'security/product_management_system_groups.xml',
        'security/ir.model.access.csv',
        'views/product_management_system_views.xml',
        'views/product_management_system_menus.xml',
        'wizard/product_add_vendor.xml',
        'wizard/product_category_change_views.xml',
        'wizard/product_update_price_views.xml',
        'wizard/product_make_purchasable_views.xml',
        'wizard/product_make_salable_views.xml',
        'wizard/product_delete_views.xml',
        'wizard/product_alternative_views.xml',
        'wizard/product_archive_views.xml',
        'wizard/product_accessory_views.xml',
        'wizard/product_optional_views.xml',
        'wizard/product_invoice_views.xml',
        'wizard/product_customer_tax_views.xml',
        'wizard/product_vendor_tax_views.xml',
        'wizard/product_publish_views.xml',
        'wizard/product_category_website_views.xml',
        'wizard/product_add_attribute_views.xml',
        'wizard/product_change_tracking_views.xml',
        'wizard/product_production_location_views.xml',
        'wizard/product_inventory_location_views.xml',
        'wizard/product_customer_lead_time_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_management_system/static/src/css/**.css',
            'product_management_system/static/src/xml/**.xml',
            'product_management_system/static/src/js/**.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
