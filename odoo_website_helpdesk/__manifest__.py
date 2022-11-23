# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Website Helpdesk Support Ticket Management V16",
    'version': '16.0.1.0.1',
    'summary': """Website Helpdesk Support Ticket Management for V16 Community""",
    'description': """Website Helpdesk Support Ticket Management for V16 Community, Helpdesk, helpdesk, support, ticket""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Website',
    'depends': ['website', 'project', 'sale_project', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk.xml',
        'views/team.xml',
        'views/res_config_settings.xml',
        'views/website_form.xml',
        'views/report.xml',
        'views/helpdesk.xml',
        'views/helpdesk_views.xml',
        'views/portal.xml',

        'data/ticket_sequence.xml',
        'data/ticket_stage_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/ticket_details.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
