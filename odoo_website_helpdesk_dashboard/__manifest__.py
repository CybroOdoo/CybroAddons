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
    'name': "Website HelpDesk Dashboard V16",
    'description': """Helpdesk Support Ticket Management Dashboard""",
    'summary': """Website HelpDesk Dashboard Module Brings a Multipurpose"""
               """Graphical Dashboard for Website HelpDesk module""",
    'version': '14.0.1.0.1',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Website',
    'depends': ['odoo_website_helpdesk', 'base'],
    'data': [
        'views/dashboard_view.xml',
        'views/dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_website_helpdesk_dashboard/static/src/css/dashboard.css',
            'odoo_website_helpdesk_dashboard/static/src/js/lib/Chart.bundle.js',
            'odoo_website_helpdesk_dashboard/static/src/xml/dashboard_view.xml',
            'odoo_website_helpdesk_dashboard/static/src/js/dashboard_view.js'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
