# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: LAJINA.K.V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class FullSettlement(models.TransientModel):
    """ Full Settlement"""
    _name = 'full.settlement'
    _description = 'Full Settlement'

    case_id = fields.Many2one('case.registration', string='Case', readonly=True,
                              help='Reference for case ')
    client_id = fields.Many2one(related='case_id.client_id', string='Client',
                                help='Client for particular case')
    lawyer_id = fields.Many2one(related='case_id.lawyer_id', string='Lawyer',
                                readonly=True,
                                help='Lawyer for particular case')
    date = fields.Date('Invoice Date', default=fields.Date.today, readonly=True,
                       help='Today date')
    cost = fields.Char('Amount', help='Invoice Amount')

    def print_invoice(self):
        """Print invoice"""
        if self.cost:
            account_move_id = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': self.date,
                'partner_id': self.client_id.id,
                'case_ref': self.case_id.name,
            }])
            account_move_id.invoice_line_ids.create([{
                'name': 'Complete Settlement',
                'quantity': 1,
                'price_unit': self.cost,
                'move_id': account_move_id.id
            }])
            self.case_id.state = 'invoiced'
            return {
                'name': "Journal Entry",
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'context': {'create': False},
                'view_mode': 'form',
                'res_id': account_move_id.id,
            }
