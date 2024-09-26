# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from . import controllers
from . import models
from . import wizard


def uninstall_hook(env):
    """Uninstall hook to delete all menu items and client actions created by the
       Advanced Dynamic Dashboard module."""
    client_actions = env['ir.actions.client'].search(
        [('tag', '=', 'AdvancedDynamicDashboard')])
    for action in client_actions:
        dashboard_menus = env['ir.ui.menu'].search([
            ('action', '=', 'ir.actions.client,%d' % action.id)
        ])
        dashboard_menus.unlink()
    client_actions.unlink()
