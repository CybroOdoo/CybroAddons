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
    'name': 'Due Date Reminder for Invoicing and Sales',
    'version': '20.0.1.0.0',
    'category': 'Sales,Accounting',
    'summary': 'Email your customers before the due date of their sale orders and unpaid invoices.',
    'description': """
     Remind your customers before their payments are due. Set a due date on
     your sale orders, and choose in the Sales and Invoicing settings how many
     days before the due date the reminders are sent: a scheduled action
     emails the customers of the sale orders that are not fully invoiced or
     paid, and of the unpaid customer invoices, and logs each reminder on
     the document.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'account'],
    'data': [
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
