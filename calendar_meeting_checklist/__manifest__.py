# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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

###############################################################################
{
    'name': "Calendar Meeting Checklist",
    'version': '15.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Enhance Meeting Preparation and Management With Checklist.',
    'description': """This module helps to enhance your meeting preparation and
     management process. It is useful to list required items, things to be done
     or points to be considered, used as a reminder in the calendar module form 
     view""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['calendar', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/meeting_checklist_views.xml',
        'views/checklist_template_views.xml',
        'views/calendar_event_views.xml',
        'wizard/import_meeting_checklist.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
