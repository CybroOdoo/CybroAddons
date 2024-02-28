# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
    'name': 'Machine Repair Management',
    'version': '16.0.1.0.0',
    'category': 'Sales,Website ,Human Resources ,Project',
    'summary': """Machine repair management is used manage the repair 
     requests ,machine diagnosis work orders and reports for repairing etc""",
    'description': """Machine Repair Management system is an application which is 
     used to  maintain the repairs of machine. It is also allow users to take 
     machine requests through website and these requests are created in the 
     backend .Also we can manage the job order,machine diagnosis and maintained 
     the team.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'hr', 'project', 'sale', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'security/base_machine_repair_management_groups.xml',
        'data/ir_sequence_data.xml',
        'data/mail_data.xml',
        'data/ir_actions_server.xml',
        'report/repair_report_templates.xml',
        'report/machine_repair_report.xml',
        'views/customer_portal_templates.xml',
        'views/customer_review_templates.xml',
        'views/machine_diagnosis_views.xml',
        'views/machine_repair_views.xml',
        'views/machine_service_type_views.xml',
        'views/machine_service_views.xml',
        'views/machine_workorder_views.xml',
        'views/product_views.xml',
        'views/repair_teams_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/website_repair_templates.xml',
        'wizard/repair_report_wizards_views.xml',
        'views/base_machine_repair_management_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
