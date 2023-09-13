# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This model extends 'res.config.settings' to add a new configuration
    parameter that controls the behavior of the Kanban view in Odoo. It
    provides the option to make the Kanban view state sticky for each user."""
    _inherit = 'res.config.settings'

    is_kanban_sticky_state = fields.Boolean(
        string="Kanban Sticky State",
        config_parameter='kanban_sticky_state.is_kanban_sticky_state',
        help="Set this field to True if you want the Kanban view state to be"
             " sticky.When this option is enabled, the last state of the "
             "Kanban view for each user will be remembered when they log in"
             " again.")
