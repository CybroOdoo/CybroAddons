# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
# ###############################################################################
from odoo import models


class MrpWorkorder(models.Model):
    """This class extends the 'mrp.workorder' model to add custom
     functionality to disable auto workorder start in Manufacturing."""
    _inherit = 'mrp.workorder'


    def action_open_mes(self):
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