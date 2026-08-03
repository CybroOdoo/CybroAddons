# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """Extension of project.task to support a custom 'New' state for bundle service components."""
    _inherit = 'project.task'

    state = fields.Selection(
        selection_add=[('00_new', 'New')],
        ondelete={'00_new': 'set default'},
    )

    @api.depends('stage_id', 'depend_on_ids.state')
    def _compute_state(self):
        """Preserve the '00_new' state when super would otherwise advance it to '01_in_progress'."""
        # Store original states to compare after super
        original_states = {task.id: task.state for task in self if task.id}
        res = super()._compute_state()
        for task in self:
            # If it was '00_new' and super tried to move it to '01_in_progress',
            # keep it as '00_new' if no blocking dependencies
            if (task.state == '01_in_progress'
                    and original_states.get(task.id) == '00_new'
                    and not task.is_blocked_by_dependences()):
                task.state = '00_new'
        return res
