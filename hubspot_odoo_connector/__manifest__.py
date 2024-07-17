# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
    'name': 'HubSpot Odoo Connector',
    'version': '17.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Connect Odoo With Hubspot',
    'description': """ This module integrates HubSpot with Odoo to sync 
    contacts, companies, and deals. It allows seamless integration between 
    HubSpot and Odoo, enabling the synchronization of important data such as
    contacts, companies, and deals between the two systems. With this connector,
    you can ensure that your customer data remains consistent and up-to-date in
    both HubSpot and Odoo, streamlining your sales and marketing processes.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['crm', 'project'],
    'data': [
        'security/hubspot_odoo_connector_groups.xml',
        'security/ir.model.access.csv',
        'views/hubspot_connector_views.xml',
        'views/hubspot_sync_history_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/crm_lead_views.xml',
    ],
    "external_dependencies": {
        'python': ['hubspot-api-client']
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
