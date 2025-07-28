# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
from odoo import models


class MrpWorkorder(models.Model):
    """This class extends the 'mrp.workorder' model to add custom
     functionality to disable auto workorder start in Manufacturing."""
    _inherit = 'mrp.workorder'


    def action_open_mes(self):
        """Opens the MES interface for the work order and starts it if needed."""
        self.ensure_one()
        if self.production_id.is_work_order:
            self.button_start()

        action = self.env['ir.actions.actions']._for_xml_id('mrp_workorder.action_mrp_display')
        action['context'] = {
            'workcenter_id': self.workcenter_id.id,
            'search_default_name': self.production_id.name,
            'shouldHideNewWorkcenterButton': True,
        }
        return action