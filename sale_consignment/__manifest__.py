# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
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

################################################################################
{
    'name': "Sale Consignment",
    'version': "16.0.1.0.0",
    'category': 'Sales',
    'summary': """This Module Helps to manage the sales order with consignment mode""",
    'description': """To create sale order with consignment option""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management', 'sale_stock', 'mail'],
    'data': ['security/sale_consignment_groups.xml',
             'security/ir.model.access.csv',
             'data/consignment_expiry_mail.xml',
             'data/sequence.xml',
             'views/sale_consignment_views.xml',
             'views/sale_consignment_line_views.xml',
             'views/res_config_settings_views.xml',
             'views/res_partner_views.xml',
             'views/product_product_views.xml',
             'views/sale_order_views.xml'],
    'images': [
        'static/description/banner.png',
    ],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
