# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Unique Sequence Number In CRM Opportunity',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Automatic sequence generation for CRM opportunities',
    'description': """This module adds automatic sequence numbers to CRM opportunities.
     It provides a dedicated sequence, assigns the code when opportunities are created,
     and backfills missing codes on module installation.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['crm'],
    'data': [
        'data/sequence_opportunity_crm_data.xml',
        'views/crm_lead_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'post_init_hook': 'assign_missing_opportunity_codes_post_init',
    'installable': True,
    'auto_install': False,
    'application': False,
}
