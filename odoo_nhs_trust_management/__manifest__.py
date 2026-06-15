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
    'name': 'NHS Trust Management',
    'version': '19.0.1.0.0',
    'category': 'Healthcare/NHS',
    'summary': 'NHS Bckoffice Operations in Odoo, Trust Management, ICBs, ICSs, Health Boards',
    'description': """NHS Trust Management - Foundation provides the core framework for managing NHS Trust governance, 
    leadership, workflows, security access, and NHS England and Scotland organizational master data within Odoo, NHS, NHS Odoo, NHS Trust Management,
    ICB Management, NHS Backoffice, NHS Operations, NHS Governance""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'mail',
        'contacts',
    ],
    'data': [
        'security/odoo_nhs_trust_management_security.xml',
        'security/ir.model.access.csv',
        'data/nhs_region_data.xml',
        'data/nhs_trust_type_data.xml',
        'data/nhs_icb_data.xml',
        'data/nhs_health_board_data.xml',
        'wizards/nhs_trust_state_change_wizard_views.xml',
        'wizards/nhs_trust_workflow_wizards_views.xml',
        'views/nhs_region_views.xml',
        'views/nhs_trust_type_views.xml',
        'views/nhs_icb_views.xml',
        'views/nhs_ics_views.xml',
        'views/nhs_health_board_views.xml',
        'views/nhs_trust_state_log_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/nhs_trust_views.xml',
        'views/nhs_trust_menus.xml',
        'views/nhs_settings_menu.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,

}
