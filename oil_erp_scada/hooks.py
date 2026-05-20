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

from odoo import SUPERUSER_ID
from odoo.fields import Command

def post_init_hook(env):
    """
    Post-init hook to assign SCADA security groups to admin and demo users.
    Based on oil_erp_base/models/res_users.py, the field name for groups
    on res.users is 'group_ids' in this environment.
    """
    group_manager = env.ref('oil_erp_scada.group_scada_manager', raise_if_not_found=False)
    group_user = env.ref('oil_erp_scada.group_scada_user', raise_if_not_found=False)
    
    admin_user = env.ref('base.user_admin', raise_if_not_found=False)
    demo_user = env.ref('base.user_demo', raise_if_not_found=False)
    
    if admin_user and group_manager:
        admin_user.write({'group_ids': [Command.link(group_manager.id)]})
    
    if demo_user and group_user:
        demo_user.write({'group_ids': [Command.link(group_user.id)]})

    # Upgrade existing Oil & Gas project storage locations to Tanks
    projects = env['project.project'].search([
        ('is_oil_gas_project', '=', True),
        ('storage_location_id', '!=', False)
    ])
    for project in projects:
        project.storage_location_id.write({
            'is_storage_tank': True,
            'tank_project_id': project.id,
        })
