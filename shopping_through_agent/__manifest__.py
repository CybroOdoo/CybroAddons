# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
    'name': 'Shopping Through Agent',
    'version': '15.0.1.0.0',
    'category': 'eCommerce',
    'summary': """Agents can shop from Website Shop onbehalf of customers.""",
    'description': """This module enable agents to create sale orders on the
    website shop on behalf for customers, streamlining the purchasing process
    and assisting customers effectively.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale','sale_management'],
    'data': [
        'data/website_menu_data.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/agent_shop_template.xml',
        'views/sale_order_portal_template.xml',
        'views/invoice_report_template.xml',
        'views/sale_order_report_template.xml',
        'views/website_sale_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
