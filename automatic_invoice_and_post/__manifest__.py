# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
    'name': 'Automatic Invoice And Post',
    'version': "17.0.1.0.0",
    'category': 'Sales,Warehouse,Accounting',
    'summary': """ Auto Invoice Generation and Auto Sending of Invoice on 
     Delivery validation.""",
    'description': """This module generates and post invoice  while validating 
    the delivery and enable to send invoice to customer
     on delivery validate .""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management', 'stock', 'account'],
    'data': ['views/res_config_settings_views.xml'],
    'license': "AGPL-3",
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False
}
