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
from . import models
from . import wizard


def create_task_stages(env):
    """
    Post-init hook to create default Oil & Gas stages using raw SQL.
    """
    # Define the stages to be created
    stages = [
        {'name': 'Planned', 'sequence': 10, 'is_oil_gas_task_stage': True, 'fold': False, 'user_id': False},
        {'name': 'Drilling', 'sequence': 20, 'is_oil_gas_task_stage': True, 'fold': False, 'user_id': False},
        {'name': 'Producing', 'sequence': 30, 'is_oil_gas_task_stage': True, 'fold': False, 'user_id': False},
        {'name': 'Shut - in', 'sequence': 40, 'is_oil_gas_task_stage': True, 'fold': False, 'user_id': False},
        {'name': 'Abandoned', 'sequence': 50, 'is_oil_gas_task_stage': True, 'fold': True, 'user_id': False},
    ]
    projects = env['project.task.type'].sudo().create(stages)
