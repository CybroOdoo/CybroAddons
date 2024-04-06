# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
    'name': 'Manufacturing Reports',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'PDF & XLS Reports For Manufacturing Module',
    'description': 'PDF & XLS reports for manufacturing module with '
                   'advanced filters.',
    'author': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'company': 'Cybrosys Techno Solutions',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/mrp_report_views.xml',
        'reports/mrp_report_templates.xml',
        'reports/mrp_report_reports.xml',
        'views/mrp_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'manufacturing_reports/static/src/js/action_manager.js',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
