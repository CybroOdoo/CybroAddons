# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import api, models


class Lead(models.Model):
    """
       Model representing a purchase order.
       This class extends the 'crm.lead' model and adds additional functionality
       specific to purchase orders.
       """
    _inherit = 'crm.lead'

    @api.model
    def get_pending_tasks(self, stage_id):
        """
            Retrieve project tasks based on a specific stage ID.
            :param stage_id: The ID of the stage to filter tasks by.
            :return: A dictionary representing an action to open project tasks.
            """
        return {
            'name': "Crm",
            'type': "ir.actions.act_window",
            'res_model': 'crm.lead',
            'domain': [('id', '=', stage_id)],
            'view_mode': "tree,form",
            'views': [[False, "tree"], [False, "form"]],
            'target': 'main',
        }
