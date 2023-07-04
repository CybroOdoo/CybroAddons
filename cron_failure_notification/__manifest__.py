# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Cron Failure Notification",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'summary': 'This module helps to notify admin on scheduled'
                'actions failures',
    'description': 'Cron Failure Notification module helps to notify the admin'
                   ' every day by mail if any cron actions failed in Odoo 15.',
    'depends': ['base', 'mail'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'report/ir_cron_failure_templates.xml',
        'report/ir_cron_reports.xml',
        'data/failure_mail_data.xml',
        'data/mail_template_data.xml',
        'views/failure_history_views.xml',
        'views/ir_cron_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
