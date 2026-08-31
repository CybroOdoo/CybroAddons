# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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
from odoo import fields, models


class QbooksLogs(models.Model):
    _name = 'qbooks.logs'
    _description = 'Qbooks Logs'
    _order = 'create_date desc'

    name = fields.Char(string="Operation", required=True,
                       help='Name of the log.')
    operation_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string="Type", required=True, help='Operation type of the log.')
    res_model = fields.Char(string="Related Model", help='Related Model of the log.')
    res_id = fields.Integer(string="Related ID", help='Related ID of the log.')
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string="Status", default='success', help='Status of the log: failed or success')
    message = fields.Text(string="Message", help='Message of the log.')
    payload = fields.Text(string="Sent Payload (JSON)", help='Payload of the log.')
    response = fields.Text(string="Response Received", help='Response')

    def action_open_record(self):
        """ Function for redirecting to the record form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }
