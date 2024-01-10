# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Odoo Drip Email Marketing',
    'version': '16.0.1.0.0',
    'category': 'Marketing',
    'summary': "Odoo Drip Email Marketing is a powerful and easy-to-use Odoo "
               "app that can help you automate your email marketing campaigns "
               "and improve your bottom line.",
    'description': """Odoo Drip Email Marketing is a powerful tool that can help
                    you automate your email marketing campaigns and reach your 
                    target audience with the right message at the right time. 
                    It's easy to use and affordable, and it's a great way to 
                    improve your customer engagement and sales.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mass_mailing'],
    'data': [
        'security/drip_mailing_history_security.xml',
        'security/drip_template_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/drip_mailing_history_views.xml',
        'views/mailing_contact_views.xml',
        'views/drip_template_views.xml',
        'views/mailing_list_templates_views.xml',
        'views/mailing_list_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
