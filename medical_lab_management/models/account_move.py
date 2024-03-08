# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from odoo import fields, models


class AccountMove(models.Model):
    """
       This class inherits the 'account.move' model to add fields for lab
       invoices.
    """
    _inherit = 'account.move'

    is_lab_invoice = fields.Boolean(string="Is Lab Invoice",
                                    help="Is it Lab Invoice or Not")
    lab_request_id = fields.Many2one('lab.appointment',
                                     string="Lab Appointment",
                                     help="Source Document")

    def _invoice_paid_hook(self):
        """
           This function extends the behavior of the 'action_post'
           method to update the state of the associated Lab Appointment to
           'invoiced' when the invoice is marked as paid.
           :param self: The record itself.
        """
        res = super(AccountMove, self)._invoice_paid_hook()
        for rec in self:
            rec.lab_request_id.write({'state': 'invoiced'})
        return res
