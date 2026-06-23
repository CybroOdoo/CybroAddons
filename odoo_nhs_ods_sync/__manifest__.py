# -*- coding: utf-8 -*-
#############################################################################
#
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
    'name': 'NHS Trust Management — ODS Sync',
    'summary': 'Sync NHS Trust records from the NHS Digital ODS portal, Odoo NHS',
    'description': """NHS Trust Management - ODS Sync,NHS,NHS Odoo, NHS Trust Management,
    ICB Management, NHS Backoffice, NHS Operations, NHS Governanceodoo, odoo nhs, odoo in nhs, odoo apps for nhs, nhs, ODOO NHS,""",
    'version': '19.0.1.0.0',
    'category': 'Healthcare/NHS',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'depends': ['odoo_nhs_trust_management'],
    'data': [
        'security/odoo_nhs_ods_sync_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/nhs_ods_role_mapping_data.xml',
        'data/ir_cron_data.xml',
        'views/nhs_ods_config_views.xml',
        'views/nhs_ods_organisation_views.xml',
        'views/nhs_ods_role_mapping_views.xml',
        'views/nhs_ods_sync_detail_views.xml',
        'views/nhs_ods_sync_run_views.xml',
        'views/nhs_ods_sync_conflict_views.xml',
        'views/nhs_trust_views_inherit.xml',
        'wizards/nhs_ods_sync_run_wizard_views.xml',
        'wizards/nhs_ods_test_connection_wizard_views.xml',
        'wizards/nhs_ods_conflict_resolve_wizard_views.xml',
        'views/nhs_ods_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'application': False,
    'installable': True,
    'auto_install': False,
}
