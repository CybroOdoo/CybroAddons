# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
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
#############################################################################
{
    'name': 'Survey Whatsapp Integration',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Send survey link through whatsapp.""",
    'description': 'This module allows users to send link and'
                   ' other details about survey through whatsapp.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['survey'],
    'data': ['security/survey_whatsapp_integration_groups.xml',
             'security/ir.model.access.csv',
             'views/survey_survey_views.xml',
             'views/configuration_manager_views.xml',
             'views/whatsapp_message_views.xml',
             'views/survey_whatsapp_integration_menu.xml',
             'wizard/survey_whatsapp_views.xml',
             'wizard/whatsapp_authenticate_views.xml',
             ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
