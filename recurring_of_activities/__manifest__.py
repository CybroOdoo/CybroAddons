# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
    'name': 'Recurring of Activities',
    'version': '15.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Using this module we can schedule activities for regular and '
               'automatic generation',
    'description': 'You can make a recurring activity for your regular'
                   ' activities using this module. You can define that when '
                   '& how activities are automatically generated.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'product', 'crm', 'account',
                'purchase', 'sale_management', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/recurring_activity_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'recurring_of_activities/static/src/js/recurring_activity.js',
        ],
        'web.assets_qweb': [
            'recurring_of_activities/static/src/xml/activity_menu_view.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
