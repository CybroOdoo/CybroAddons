# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Renjith (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Education ERP Dashboard',
    'version': '15.0.1.0.0',
    'category': 'Industries, Productivity',
    'summary': 'An integrated view of the education ERP system',
    'description': """A comprehensive module designed to provide educational
    institutions to manage and monitor various operations""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'education_attendances', 'education_promotion',
                'education_time_table'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_tag_views.xml',
        'views/erp_dashboard_menu.xml'],
    'assets': {
        'web.assets_backend': [
            'education_erp_dashboard/static/src/js/dashboard.js',
            'education_erp_dashboard/static/src/css/dashboard.css',
            'https://cdn.jsdelivr.net/npm/chart.js'
        ],
        'web.assets_qweb': [
            'education_erp_dashboard/static/src/xml/dashboard_templates.xml',
            'education_erp_dashboard/static/src/xml/dashboard_content_templates.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
