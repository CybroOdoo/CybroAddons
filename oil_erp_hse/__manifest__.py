# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Oil & Gas HSE',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP',
    'summary': 'Health, Safety & Environment Management for Oil & Gas',
    'description': """
HSE module for upstream oil & gas operations.
- Incident & Near-Miss Reporting
- HSE Inspections & Checklists
- Work Permits (Hot Work, Confined Space, etc.)
- Risk Assessments
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_project',
        'oil_erp_equipment',
        'mail',
        'maintenance',
        'project',
    ],
    'data': [
        'security/oil_hse_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/oil_hse_incident_views.xml',
        'views/oil_hse_inspection_views.xml',
        'views/oil_hse_permit_views.xml',
        'views/oil_hse_risk_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/project_task_type_views.xml',
        'views/hse_reporting_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'create_task_stages',
}
