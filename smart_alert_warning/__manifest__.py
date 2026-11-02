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
    'name': 'Smart Alerts',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Smart Alerts, Form Alert, Warning Banner, Conditional Alert, Record Warning, Alert Message, Odoo Alert, Odoo20 Alert, Odoo20 Warning""",
    'description': """
     Show alert banners on the form view of any model. An admin configures
     the message, its style (info, success, warning, danger...), the form
     view to show it on, the records it applies to with a filter, and
     optionally the group of users who see it. The alert appears above the
     form and shows or hides live while the record is edited.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'security/smart_alert_warning_groups.xml',
        'security/ir.access.csv',
        'views/alert_message_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
