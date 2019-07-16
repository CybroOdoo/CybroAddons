# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Cron Job Failure Notification",
    'summary': """Cron jobs/Scheduled Actions failure Log Notification & Its PDF Reports""",
    'description': """
        This module will generate error Logs for Scheduled
        Actions / Cron jobs running in backend server
    """,
    'author': "Cybrosys Techno Solution",
    'website': "https://www.cybrosys.com",
    'category': 'Extra Tools',
    'depends': ['base', 'mail', 'web', 'base_setup'],
    'data': [
        'views/logs_scheduled_actions_view.xml',
        'views/error_log_report_template.xml',
        'views/report.xml',
        'views/error_mail_template.xml',
    ],
    'demo': [
        'demo/ir_cron_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
