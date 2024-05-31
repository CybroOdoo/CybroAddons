# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models, _


class PestRequest(models.Model):
    """ This model represents requests related to pest management within the
    context of agriculture. It provides a structured way to initiate and manage
    requests for pest control measures, treatments, and interventions."""
    _name = 'pest.request'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Pest Request In Agriculture Management'
    _rec_name = 'reference'

    reference = fields.Char(string='Reference', help='Mention the details of '
                                                     'pesticide request',
                            copy=False, readonly=True, tracking=True,
                            default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date', tracking=True,
                               help='The date the pesticide request was sent.',
                               default=fields.Date.context_today, required=True)
    farmer_id = fields.Many2one('farmer.detail', string='Farmer',
                                help='Mention the corresponding farmer that '
                                     'request send', required=True,
                                tracking=True)
    crop_id = fields.Many2one('crop.request', string='Crop',
                              help='Mention the corresponding crop the '
                                   'pesticide needed', required=True,
                              tracking=True)
    pest_id = fields.Many2one('pest.detail', string='Pest',
                              help='Mention the pesticide name Required ',
                              required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
                            'environment.',
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help='Currency used by the company',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    pest_quantity = fields.Integer(string='Pest Quantity', tracking=True,
                                   help='The quantity of pesticide that is'
                                        'required to be purchased',
                                   required=True)
    pest_cost = fields.Float(string='Pest Cost', required=True,
                             help="The unit price of the pesticide",
                             tracking=True, related='pest_id.pest_cost')
    total_cost = fields.Float(string='Total Cost', tracking=True, store=True,
                              help="The total cost of the pesticide that was "
                                   "purchased.", compute='_compute_total_cost')
    disease = fields.Text(string='Disease', tracking=True, required=True,
                          help="The corresponding disease of crop")
    note = fields.Text(string='Note', tracking=True,
                       help="Please describe any additional details here if "
                            "there is a need to mention additional data.")
    state = fields.Selection(
        [('draft', 'Draft'), ('pending', 'Pending'), ('approve', 'Approved'),
         ('rejected', 'Rejected'), ('paid', 'Paid')], string='Status',
        default='draft', tracking=True, copy=False,
        help=" The status of pesticide request")
    pest_paid_bool = fields.Boolean(string='Paid Bool', default=False,
                                    copy=False)

    def action_draft(self):
        """ Function for change state of crop request to cancel """
        self.state = 'draft'

    def action_pending(self):
        """ Function for change state of pest request to pending """
        self.state = 'pending'

    def action_approved(self):
        """ Function for change state of pest request to approve """
        self.state = 'approve'

    def action_create_invoice(self):
        """Method for creating invoice for the pesticides"""
        create_invoice = self.env['account.move'].create({
            'partner_id': self.farmer_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {'name': self.pest_id.pest_name,
                                         'price_unit': self.total_cost})]
        })
        create_invoice.action_post()
        if create_invoice.payment_state == 'paid':
            self.pest_paid_bool = True
            self.state = 'paid'
        return {
            'name': 'Customer Invoice',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_id': create_invoice.id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
        }

    def action_rejected(self):
        """ Function for change state of pest request to rejected """
        self.state = 'rejected'

    @api.depends('pest_cost', 'pest_quantity')
    def _compute_total_cost(self):
        """Function for calculate total cost of pesticide"""
        for record in self:
            record.total_cost = record.pest_cost * record.pest_quantity

    @api.model
    def create(self, values):
        """ Function for create new pest request """
        if values.get('reference', _('New')) == _('New'):
            values['reference'] = self.env['ir.sequence'].next_by_code(
                'pest.request') or _('New')
        res = super(PestRequest, self).create(values)
        return res
