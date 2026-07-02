# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (<https://www.cybrosys.com>)
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
    'name': 'Mailchimp Marketing Connector',
    'version': '17.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'summary': 'Synchronize your contact list,campaign an templates.',
    'description': """This module helps to synchronize your contact list, 
     campaign, templates between Odoo and MailChimp.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/mailchimp_account_views.xml',
        'views/mailchimp_mailing_list_views.xml',
        'views/mailing_list_views.xml',
        'wizards/mailchimp_operations_views.xml',
        'views/mailchimp_marketing_connector_menus.xml',
        'views/mailchimp_template_views.xml',
        'views/mailing_mailing_views.xml'
    ],
    'external_dependencies': {'python': ['mailchimp-marketing']},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
