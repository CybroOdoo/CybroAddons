#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ClaimDetails(models.Model):
    """Claims registered against confirmed insurances."""
    _name = 'claim.details'
    _description = "Claim Details"
    _inherit = ['mail.thread']
    _check_company_auto = True

    name = fields.Char(copy=False, readonly=True, index=True,
                       default=lambda self: self.env._('New'),
                       help="Sequence for claim details")
    insurance_id = fields.Many2one(
        'insurance.details', required=True, index=True, check_company=True,
        domain=[('state', '=', 'confirmed')], tracking=True,
        help="Only confirmed insurances can be selected")
    company_id = fields.Many2one(
        related='insurance_id.company_id', store=True, index=True,
        help="Company of the insurance")
    partner_id = fields.Many2one(related='insurance_id.partner_id',
                                 string='Customer',
                                 help="Partner related to insurance")
    policy_id = fields.Many2one(related='insurance_id.policy_id',
                                string='Policy',
                                help="Policy related to insurance")
    employee_id = fields.Many2one(related='insurance_id.employee_id',
                                  string='Agent',
                                  help="Agent related to insurance")
    currency_id = fields.Many2one(
        related='insurance_id.currency_id', string='Currency',
        help="Currency of the insurance")
    amount = fields.Monetary(
        compute='_compute_amount', store=True, readonly=False,
        precompute=True, tracking=True,
        help="Claimed amount. By default, the part of the insured amount "
             "not claimed yet")
    state = fields.Selection(related='insurance_id.state',
                             string='Insurance State')
    date_claimed = fields.Date(string='Date Applied',
                               default=fields.Date.context_today,
                               help="Date on which the claim was applied")
    invoice_id = fields.Many2one('account.move', string='Bill',
                                 readonly=True, copy=False,
                                 help="Bill related to the claim")
    # Computed with sudo so users without Invoicing access can still read this flag.
    can_create_bill = fields.Boolean(
        compute='_compute_can_create_bill', compute_sudo=True,
        help="Set when a settlement bill can be generated for the claim")
    has_bill = fields.Boolean(
        compute='_compute_has_bill', compute_sudo=True,
        help="Indicates whether a settlement bill exists for the claim")
    note_field = fields.Html(string='Comment',
                             help="Extra notes for the claim")

    @api.depends('insurance_id')
    def _compute_amount(self):
        """Default the amount to what is left to claim on the insurance."""
        for claim in self:
            others = claim.insurance_id.claim_ids.filtered(
                lambda c: c.id != claim._origin.id)
            claim.amount = max(
                claim.insurance_id.amount - sum(others.mapped('amount')), 0.0)

    @api.depends('state', 'invoice_id.state')
    def _compute_can_create_bill(self):
        """A confirmed claim without an active bill can be settled."""
        for claim in self:
            claim.can_create_bill = (
                claim.state == 'confirmed'
                and (not claim.invoice_id
                     or claim.invoice_id.state == 'cancel'))

    @api.depends('invoice_id')
    def _compute_has_bill(self):
        """Indicate whether an invoice/bill is linked to the claim."""
        for claim in self:
            claim.has_bill = bool(claim.invoice_id)

    @api.constrains('amount', 'insurance_id')
    def _check_amount(self):
        """The claims of an insurance cannot exceed the insured amount."""
        for claim in self:
            if claim.amount <= 0:
                raise ValidationError(self.env._(
                    "The claimed amount should be greater than zero."))
            insurance = claim.insurance_id
            total = sum(self.search(
                [('insurance_id', '=', insurance.id)]).mapped('amount'))
            if insurance.currency_id.compare_amounts(
                    total, insurance.amount) > 0:
                raise ValidationError(self.env._(
                    "The claims of %(insurance)s total %(total)s, which "
                    "exceeds the insured amount of %(amount)s.",
                    insurance=insurance.name,
                    total=insurance.currency_id.format(total),
                    amount=insurance.currency_id.format(insurance.amount)))

    @api.model_create_multi
    def create(self, vals_list):
        """Function to create sequence"""
        for vals in vals_list:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'claim.details') or self.env._('New')
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_billed(self):
        """Block the deletion of a claim that already has a bill."""
        if self.filtered('invoice_id'):
            raise UserError(self.env._(
                "A claim with a settlement bill cannot be deleted."))

    def action_create_bill(self):
        """Create the settlement vendor bill of the claim and open it."""
        self.ensure_one()
        self.env['account.move'].check_access('create')
        if self.state != 'confirmed':
            raise UserError(self.env._(
                "Bills can only be created for claims on confirmed "
                "insurances."))
        if self.invoice_id and self.invoice_id.state != 'cancel':
            raise UserError(self.env._(
                "A bill has already been created for this claim."))
        bill = self.env['account.move'].with_company(self.company_id).create({
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.env.user.id,
            'claim_id': self.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [fields.Command.create({
                'name': self.env._(
                    "Insurance claim %(claim)s", claim=self.name),
                'quantity': 1,
                'price_unit': self.currency_id.round(self.amount),
            })],
        })
        self.invoice_id = bill
        return bill._get_records_action()
