# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(v11)
#	     Akshay Babu(v12)(<https://www.cybrosys.com>)
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
    'name': 'User Login Alert',
    'summary': """Secure your Odoo account by alerts at right time. If any successful login to your
                account happens, an alert mail will be send to you with the browser and IP details.""",
    'version': '12.0.1.0.0',
    'description': """Secure your Odoo account by alerts at right time. If any successful login to your
                    account happens, an alert mail will be send to you with the browser and IP details.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Tools',
    'depends': ['base', 'mail'],
    'license': 'AGPL-3',
    'data': [
        'security/notification_group.xml',
        'views/logged_details_view.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['httpagentparser'],
    },


}

