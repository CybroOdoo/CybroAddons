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
    'name': "Website HelpDesk Dashboard",
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """Helpdesk Support Ticket Management Dashboard""",
    'description': """Website HelpDesk Dashboard Module Brings a Multipurpose"""
                   """Graphical Dashboard for Website HelpDesk module""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['odoo_website_helpdesk', 'base'],
    'data': [
        'views/menu_item.xml',
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
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False,
}
