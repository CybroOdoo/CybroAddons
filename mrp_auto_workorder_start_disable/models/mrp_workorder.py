# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class MrpWorkorder(models.Model):
    """This class extends the 'mrp.workorder' model to add custom
     functionality to disable auto workorder start in Manufacturing."""
    _inherit = 'mrp.workorder'

    def open_tablet_view(self):
        """By default, return tablet view without starting workorder."""
        self.ensure_one()
        if self.production_id.is_work_order:
            return super().open_tablet_view()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mrp_workorder.tablet_client_action")
        action['target'] = 'fullscreen'
        action['res_id'] = self.id
        action['context'] = {
            'active_id': self.id,
            'from_production_order': self.env.context.get(
                'from_production_order'),
            'form_view_initial_mode': 'edit',
            'from_manufacturing_order': self.env.context.get(
                'from_manufacturing_order')
        }
        return action

    def button_initial(self):
        """Start button when auto start is disabled."""
        self.ensure_one()
        self.button_start()
