# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Odoo Advanced Chatter',
    'version': '16.0.2.0.0',
    'category': 'Discuss',
    'summary': 'Schedule Log note and Send Message in Chatter',
    'description': """We have the capability to schedule log notes and send 
                    messages within Chatter.Additionally, followers can be 
                    managed both from the followers list and directly within 
                    the Schedule form.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/schedule_log_view.xml',
        'wizard/mail_wizard_recipients_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'odoo_advanced_chatter/static/src/xml/schedule_log.xml',
            'odoo_advanced_chatter/static/src/js/schedule_mail.js',
            'odoo_advanced_chatter/static/src/xml/follower_list.xml',
            'odoo_advanced_chatter/static/src/js/follower_list.js',
            'odoo_advanced_chatter/static/src/xml/chatter.xml',
            'odoo_advanced_chatter/static/src/js/composer.js',
        ]
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'license': 'LGPL-3',
    'auto_install': False,
    'application': False,
}
