# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CaseRegistration(models.Model):
    """Case registration and invoice for trials and case"""
    _name = 'case.registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Case Register'

    name = fields.Char('Case No', readonly=True, default=lambda self: _('New'),
                       help='Case number')
    client_id = fields.Many2one('res.partner', string='Client', required=True,
                                help='Clients in the law firm')
    email = fields.Char(related="client_id.email", required=True, string='Email',
                        help='Email of client', readonly=False)
    contact_no = fields.Char(related="client_id.phone", required=True,
                             string='Contact No', readonly=False)
    payment_method = fields.Selection(selection=[
        ('trial', "Per Trial"),
        ('case', "Per Case"),
        ('out_of_court', "Out of Court")], string='Payment Method',
        states={'draft': [('invisible', True)]})
    lawyer_wage = fields.Char(invisible=True)
    lawyer_id = fields.Many2one('hr.employee', string='Lawyer',
                                domain=[('is_lawyer', '=', True),
                                        ('parent_id', '=', False)],
                                help="Lawyers in the law firm")
    lawyer_unavailable = fields.Boolean(default=False)
    junior_lawyer_id = fields.Many2one('hr.employee', string='Junior Lawyer',
                                       help='Juniors lawyers in the law firm')
    court_id = fields.Many2one('legal.court', string='Court',
                               help="Name of courts")
    court_no_required = fields.Boolean(help='Makes court as Not required field',
                                       default=True)
    judge_id = fields.Many2one(related='court_id.judge_id', string='Judge',
                               store=True, help="Available judges")
    register_date = fields.Date('Registration Date', required=True,
                                default=fields.Date.today,
                                help='Case registration date')
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date')
    case_category_id = fields.Many2one('case.category', 'Case Category',
                                       required=True,
                                       help="Category of case")
    description = fields.Html('Description', required=True,
                              help="Case Details")
    opposition_name = fields.Char('Name', help="Name of Opposite Party")
    opposite_lawyer = fields.Char('Lawyer', help="Name of opposite Lawyer")
    opp_party_contact = fields.Char('Contact No')
    victim_ids = fields.One2many('case.victim', 'registration_id',
                                 help="List of Victims")
    sitting_detail_ids = fields.One2many('case.sitting', 'case_id')
    evidence_count = fields.Integer(compute='_compute_evidence_count',
                                    help="Count of evidence")
    case_attachment_count = fields.Integer(
        compute='_compute_case_attachment_count',
        help="Count of attachments")
    trial_count = fields.Integer(compute='_compute_trial_count',
                                 help="Count of trials")
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   help="Count of Invoices")
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'),
         ('invoiced', 'Invoiced'), ('reject', 'Reject'),
         ('won', 'Won'), ('lost', 'Lost'), ('cancel', 'Cancel')],
        string='State', default='draft')
    company_id = fields.Many2one("res.company", string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True)

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        """Court not required based on,
         - if payment method = out of court
         - if invoice through full settlement"""
        if self.payment_method == 'out_of_court':
            self.court_no_required = False
        else:
            self.court_no_required = True

    @api.onchange('lawyer_id')
    def _onchange_lawyer_id(self):
        """lawyer unavailable warning and lists his juniors"""
        cases = self.sudo().search(
            [('lawyer_id', '=', self.lawyer_id.id), ('state', '!=', 'draft'),
             ('id', '!=', self._origin.id)])
        self.lawyer_id.not_available = False
        self.lawyer_unavailable = False
        if self.lawyer_id:
            for case in cases:
                if case.end_date and case.end_date <= fields.Date.today():
                    self.lawyer_id.not_available = False
                    self.lawyer_unavailable = False
                else:
                    self.lawyer_id.not_available = True
                    self.lawyer_unavailable = True
                    break
            if self.lawyer_unavailable:
                return {
                    'warning': {
                        'title': 'Lawyer Unavailable',
                        'message': 'The selected lawyer is unavailable '
                                   'at this time.'
                                   'You can choose his juniors.',
                    },
                    'domain': {
                        'junior_lawyer_id': [('parent_id', '=',
                                              self.lawyer_id.id),
                                             ('is_lawyer', '=', True)],
                    },
                }

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Records can be deleted only draft and cancel state"""
        case_records = self.filtered(
            lambda x: x.state not in ['draft', 'cancel'])
        if case_records:
            raise UserError(_(
                "You can not delete a Approved Case."
                " You must first cancel it."))

    def action_full_settlement(self):
        """Returns the full settlement view"""
        self.court_no_required = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'full.settlement',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id}
        }

    def action_cancel(self):
        """State changed to cancel"""
        self.write({'state': 'cancel'})
        self.lawyer_id.not_available = False
        self.end_date = fields.Date.today()

    def action_reset_to_draft(self):
        """ Stage reset to draft"""
        self.write({'state': 'draft'})

    def action_confirm(self):
        """Confirmation of Cases"""
        if self.name == 'New':
            self.name = self.env['ir.sequence']. \
                            next_by_code('case_registration') or 'New'
        self.state = 'in_progress'

    def action_reject(self):
        """Rejection of Cases"""
        self.write({'state': 'reject'})

    def validation_case_registration(self):
        """Show Validation Until The Lawyer Details are Filled"""
        if not self.lawyer_id:
            raise ValidationError(_(
                """Please assign a lawyer for the case"""
            ))

    def action_invoice(self):
        """button method to show invoice wizard"""
        if not self.payment_method:
            raise ValidationError(_(
                """Please select a payment method for create invoice"""
            ))
        if self.payment_method == 'case':
            self.lawyer_wage = self.lawyer_id.wage_per_case
        elif self.payment_method == 'trial':
            self.lawyer_wage = self.lawyer_id.wage_per_trial
        else:
            self.lawyer_wage = ''
        self.validation_case_registration()
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id,
                        'default_cost': self.lawyer_wage}
        }

    def action_evidence(self):
        """Button to add evidence"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'form',
            'res_model': 'legal.evidence',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def get_attachments(self):
        """Show attachments in smart tab which added in chatter"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', self._name)],
            'context': {'create': False}
        }

    def _compute_case_attachment_count(self):
        """Compute the count of attachments"""
        for attachment in self:
            attachment.case_attachment_count = self.env['ir.attachment']. \
                sudo().search_count([('res_id', '=', self.id),
                                     ('res_model', '=', self._name)])

    def action_won(self):
        """Changed to won state"""
        self.state = 'won'
        self.end_date = fields.Date.today()
        self.lawyer_id.not_available = False

    def action_lost(self):
        """Changed to lost state"""
        self.state = 'lost'
        self.end_date = fields.Date.today()
        self.lawyer_id.not_available = False

    def _compute_evidence_count(self):
        """Computes the count of evidence"""
        for case in self:
            case.evidence_count = case.env['legal.evidence'].search_count(
                [('client_id', '=', self.client_id.id),
                 ('case_id', '=', self.id)])

    def _compute_trial_count(self):
        """Compute the count of trials"""
        for case in self:
            case.trial_count = case.env['legal.trial']. \
                search_count([('client_id', '=', self.client_id.id),
                              ('case_id', '=', self.id)])

    def action_trial(self):
        """Button to add trial"""
        self.validation_case_registration()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'form',
            'res_model': 'legal.trial',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def _compute_invoice_count(self):
        """Calculate the count of invoices"""
        for inv in self:
            inv.invoice_count = self.env['account.move'].search_count(
                [('case_ref', '=', self.name)])

    def get_invoice(self):
        """Get the corresponding invoices"""
        return {
            'name': 'Case Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('case_ref', '=', self.name)],
        }

    def get_evidence(self):
        """Returns the evidences"""
        evidence_ids_list = self.env['legal.evidence']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'tree,form',
            'res_model': 'legal.evidence',
            'domain': [('id', 'in', evidence_ids_list)],
            'context': "{'create': False}"
        }

    def get_trial(self):
        """Returns the Trials"""
        trial_ids_list = self.env['legal.trial']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'tree,form',
            'res_model': 'legal.trial',
            'domain': [('id', 'in', trial_ids_list)],
            'context': "{'create': False}"
        }
