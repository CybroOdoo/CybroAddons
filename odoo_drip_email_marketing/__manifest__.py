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
    'name': 'Odoo Drip Email Marketing',
    'version': '20.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Send a welcome mail to new subscribers and scheduled drip mails to the contacts of your mailing lists.',
    'description': """
     Automate the emails of your mailing lists. Send a welcome template to
     the contacts who subscribe to a list, and a sequence of drip templates
     to all its contacts, each a given number of days after the start date
     of the campaign, through the chosen outgoing mail server. Every drip
     sent is logged in the drip history of the list and of the contact.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mass_mailing'],
    'data': [
        'security/ir.access.csv',
        'data/ir_cron_data.xml',
        'views/drip_mailing_history_views.xml',
        'views/mailing_contact_views.xml',
        'views/drip_template_views.xml',
        'views/mailing_list_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
