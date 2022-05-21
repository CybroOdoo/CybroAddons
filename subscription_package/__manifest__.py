# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Subscription Management For Community',
    'Version': '15.0.1.0.0',
    'summary': 'Subscription Package Management Module For Odoo15 Community',
    'description': 'Subscription Package Management Module For Odoo15 Community',
    'category': 'Sales',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/uom_demo.xml',
        'data/subscription_stage_data.xml',
        'data/mail_template.xml',
        'data/cron.xml',
        'wizard/subscription_close_wizard.xml',
        'views/subscription_package.xml',
        'views/subscription_products.xml',
        'views/subscription_plan.xml',
        'views/subscription_stage.xml',
        'views/subscription_close.xml',
        'views/subscription_renew.xml',
        'views/mail_activity_views.xml',
        'views/res_partner.xml',
        'report/subscription_report_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
