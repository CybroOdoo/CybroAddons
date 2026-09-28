# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#############################################################################
{
    "name": "CS-Cart Connector",
    "version": "19.0.1.0.0",
    "category": "Integration",
    "summary": "CS-Cart Odoo Connector",
    "description": """CS-Cart Odoo Connector module allows to connect with CS-Cart e-commerce store and sync products, categories, customers, orders, and inventory with Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["sale", "stock", "delivery", "queue_job"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_category.xml",
        "data/sale_order_cron_job.xml",
        "data/customer_sync_cron_job.xml",
        "data/product_sync_cron_job.xml",
        "data/vendor_sync_cron_job.xml",
        "data/export_product_server_action.xml",
        "data/export_category_server_action.xml",
        "data/export_res_partner_server_action.xml",
        "data/export_sale_order_server_action.xml",
        "views/cs_cart_config_views.xml",
        "views/cs_cart_import_batch_views.xml",
        "views/cs_cart_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_cscart_connector/static/src/js/cs_cart_connector.js",
            "odoo_cscart_connector/static/src/css/cs_cart_connector.css",
            "odoo_cscart_connector/static/src/xml/cs_cart_connector.xml",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,

}
