# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Dhanya B(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'CRM Duplicates Real Time Search',
    'version': '16.0.1.0.0',
    'summary': """This Module Allows us to prevent making duplicated contacts 
    and leads as well as display message regarding the duplication.""",
    'description': 'This module facilitates the prevention of creating'
                   ' duplicate contacts and leads within the system. '
                   'It achieves this by implementing mechanisms to identify'
                   ' potential duplicates based on fields. When a user '
                   'attempts to create a new contact or lead that matches an'
                   ' existing record, the module triggers a notification '
                   'alerting the user about the potential duplication.'
                   'This message prompts the user to review the existing '
                   'records before proceeding, ensuring data integrity and '
                   'minimizing redundancy in the database.that are attached to'
                   'the products from website',
    'category': 'CRM',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['crm', 'contacts', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
