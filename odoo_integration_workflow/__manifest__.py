# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions @cybrosys(odoo@cybrosys.com)
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
    'name': 'Odoo Integration Workflow',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'A powerful no-code visual designer for Odoo that enables users to build, automate, and test complex API integrations and ORM operations using an interactive drag-and-drop canvas, advanced logic branching, and dynamic data mapping.',
    'description': """
        Odoo Integration Workflow is a powerful no-code ETL tool featuring a visual drag-and-drop 
        canvas to design complex API integrations and Odoo automations using REST requests (GET/POST/PUT/DELETE),
         ORM operations, loops, and conditional branching. Seamlessly sync data with external systems using dynamic 
         variable mapping, triggered automatically via scheduled Crons or real-time record events.
    """,
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web' , 'base_automation'],
    'data': [
        'views/workflow_views.xml',
        'views/workflow_test_result.xml',
        'views/workflow_menu.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_integration_workflow/static/src/xml/*',
            'odoo_integration_workflow/static/src/css/*',
            'odoo_integration_workflow/static/src/js/*',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
