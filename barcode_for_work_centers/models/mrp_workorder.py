# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jaseem (odoo@cybrosys.com)
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


class MrpWorkOrder(models.Model):
    """This class represents the inheriting add the all rpc function for js
    such as action_work_order_start_stop,action_puase,action_continue and
    action_done"""
    _inherit = "mrp.workorder"

    def action_work_order_start_stop(self, clicked_record, man_order):
        """This function is used to start and stop the work order after scanning
         barcode in barcode template , it returns the message that 'start' or '
         stop'."""
        record = self.env["mrp.routing.workcenter"].browse(int(clicked_record))
        mrp_order = self.env["mrp.production"].search(
            [("name", "=", man_order)])
        params_for_template = {}
        if record.workorder_ids and mrp_order:
            for wo in record.workorder_ids:
                if wo.production_id.id == mrp_order.id:
                    if wo.production_state not in ['draft', 'done',
                                                   'cancel', ] and \
                            wo.working_state != "blocked" and wo.state not in \
                            ["done", "cancel", "progress"]:
                        wo.button_start()
                        params_for_template.update(
                            {"pop_up": "start", "duration": wo.duration})
                    elif wo.state != "done":
                        wo.button_finish()
                        params_for_template.update({"pop_up": "end"})
                    elif wo.state == "done":
                        params_for_template.update({"pop_up": "already done"})
                    else:
                        params_for_template.update({"pop_up": "not match"})
        else:
            params_for_template.update({"pop_up": "not match"})
        return params_for_template

    def action_pause(self, clicked_record, man_order):
        """This function is used to perform action pause  while clicking the
        pause button from barcode scanning template """
        record = self.env["mrp.routing.workcenter"].browse(int(clicked_record))
        mrp_order = self.env["mrp.production"].search(
            [("name", "=", man_order)])
        if record.workorder_ids and mrp_order:
            for wo in record.workorder_ids:
                if wo.production_id.id == mrp_order.id:
                    wo.button_pending()
                    return "paused"

    def action_continue(self, clicked_record, man_order):
        """This function is used to continue the work order after clicking the
        continue button"""
        record = self.env["mrp.routing.workcenter"].browse(int(clicked_record))
        mrp_order = self.env["mrp.production"].search(
            [("name", "=", man_order)])
        if record.workorder_ids and mrp_order:
            for wo in record.workorder_ids:
                if wo.production_id.id == mrp_order.id:
                    wo.button_start()
                    return "continue"

    def action_done(self, clicked_record, man_order):
        """This function is used to stop the work order after clicking the
            done button"""
        record = self.env["mrp.routing.workcenter"].browse(int(clicked_record))
        mrp_order = self.env["mrp.production"].search(
            [("name", "=", man_order)])
        if record.workorder_ids and mrp_order:
            for wo in record.workorder_ids:
                if wo.production_id.id == mrp_order.id:
                    wo.button_finish()
                    return "done"
