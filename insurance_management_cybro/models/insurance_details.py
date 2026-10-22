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


class InsuranceDetails(models.Model):
    """Insurances issued to customers, invoiced in full or by installments."""
    _name = 'insurance.details'
    _description = "Insurance Details"
    _inherit = ['mail.thread']
    _check_company_auto = True

    _policy_number_uniq = models.Constraint(
        'unique(company_id, policy_number)',
        'The policy number must be unique per company.',
    )
    _policy_number_positive = models.Constraint(
        'CHECK(policy_number > 0)',
        'The policy number must be greater than zero.',
    )
    _policy_duration_positive = models.Constraint(
        'CHECK(policy_duration > 0)',
        'The duration must be at least one month.',
    )

    name = fields.Char(required=True, copy=False, readonly=True,
                       index=True, default=lambda self: self.env._('New'),
                       help="Sequence of insurance created")
    company_id = fields.Many2one(
        'res.company', required=True, index=True,
        default=lambda self: self.env.company,
        help="Company issuing the insurance")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True, check_company=True,
                                 tracking=True,
                                 help="Partner related to insurance")
    start_date = fields.Date(string='Date Started', required=True,
                             default=fields.Date.context_today,
                             help="Start date of insurance")
    close_date = fields.Date(string='Date Closed', readonly=True,
                             help="End date of insurance")
    invoice_ids = fields.One2many('account.move', 'insurance_id',
                                  string='Invoices', readonly=True,
                                  help="Invoices related to insurance")
    claim_ids = fields.One2many('claim.details', 'insurance_id',
                                string='Claims', readonly=True,
                                help="Claims registered on the insurance")
    employee_id = fields.Many2one('employee.details', string='Agent',
                                  required=True, check_company=True,
                                  help="Agent related to the insurance")
    commission_rate = fields.Float(string='Commission Percentage',
                                   help="Commission rate of the agent, as a "
                                        "percentage between 0 and 100")
    policy_id = fields.Many2one('policy.details', required=True,
                                check_company=True, tracking=True,
                                help="Select the policy details "
                                     "and the policy preferred")
    policy_payment_type_ids = fields.Many2many(
        'payment.type',
        related='policy_id.payment_type_ids',
        string="Allowed Payment Types",
    )
    payment_type_id = fields.Many2one(
        'payment.type',
        domain="[('id', 'in', policy_payment_type_ids)]",
        help="Select the payment type allowed by the policy")
    is_fixed_payment = fields.Boolean(
        compute='_compute_is_fixed_payment',
        help="Set when the selected payment type is a fixed payment")
    policy_duration = fields.Integer(
        string='Duration in months', required=True,
        help="Duration of the insurance in months, which is also the "
             "number of installments")
    currency_id = fields.Many2one(
        related='policy_id.currency_id', string='Currency',
        help="Currency of the policy")
    amount = fields.Monetary(related='policy_id.amount', string='Amount',
                             help="The amount for the policy based "
                                  "on policy selected")
    amount_installment = fields.Monetary(
        string="Installment Amount", compute="_compute_amount_installment",
        help="Amount of each installment of the policy")
    # Computed with sudo so users without Invoicing access can still read the amount.
    amount_remaining = fields.Monetary(
        string='Amount remaining', compute='_compute_amount_remaining',
        compute_sudo=True,
        help="Part of the policy amount that is not invoiced yet")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('closed', 'Closed')],
                             required=True, default='draft', tracking=True,
                             copy=False, help="State of insurance")
    # Computed with sudo so users without Invoicing access can still read this flag.
    can_create_invoice = fields.Boolean(
        compute='_compute_can_create_invoice', compute_sudo=True,
        help="Set when the insurance is confirmed and not fully invoiced")
    note_field = fields.Html(string='Comment', help="Additional notes about the insurance")
    policy_number = fields.Integer(
        required=True, copy=False,
        help="Policy number is a unique number that an insurance company "
             "uses to identify you as a policyholder")

    @api.onchange('policy_id')
    def _onchange_policy_id(self):
        """Reset the payment type if the new policy does not allow it."""
        allowed = self.policy_id.payment_type_ids
        if self.payment_type_id and self.payment_type_id not in allowed:
            self.payment_type_id = False

    @api.depends('payment_type_id')
    def _compute_is_fixed_payment(self):
        """Whether the selected payment type is the fixed lump sum."""
        fixed = self.env.ref('insurance_management_cybro.payment_type_fixed',
                             raise_if_not_found=False)
        for record in self:
            record.is_fixed_payment = bool(
                fixed and record.payment_type_id == fixed)

    @api.depends('amount', 'policy_duration')
    def _compute_amount_installment(self):
        """Amount of one installment, from the total and the duration."""
        for record in self:
            if record.policy_duration > 0:
                record.amount_installment = record.currency_id.round(
                    record.amount / record.policy_duration)
            else:
                record.amount_installment = 0.0

    def _get_active_invoices(self):
        """Customer invoices that count against the policy amount."""
        return self.invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice' and m.state != 'cancel')

    @api.depends('amount', 'invoice_ids.amount_total', 'invoice_ids.state',
                 'invoice_ids.move_type')
    def _compute_amount_remaining(self):
        """Policy amount minus the open or posted invoices, plus the
        posted credit notes."""
        for record in self:
            invoiced = sum(
                record._get_active_invoices().mapped('amount_total'))
            refunded = sum(record.invoice_ids.filtered(
                lambda m: m.move_type == 'out_refund' and m.state == 'posted',
            ).mapped('amount_total'))
            record.amount_remaining = record.amount - invoiced + refunded

    @api.depends('state', 'amount_remaining')
    def _compute_can_create_invoice(self):
        """A confirmed insurance with an amount left can be invoiced."""
        for record in self:
            record.can_create_invoice = (
                record.state == 'confirmed'
                and record.currency_id.compare_amounts(
                    record.amount_remaining, 0.0) > 0)

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        """Ensure the commission percentage is between 0 and 100."""
        if self.filtered(lambda rec: not 0 <= rec.commission_rate <= 100):
            raise ValidationError(self.env._(
                'Commission Percentage should be between 0 and 100'))

    @api.model_create_multi
    def create(self, vals_list):
        """Function to create sequence"""
        for vals in vals_list:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'insurance.details') or self.env._('New')
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirmed(self):
        """Block the deletion of an insurance that is not a draft."""
        if self.filtered(lambda rec: rec.state != 'draft'):
            raise UserError(self.env._(
                "Only draft insurances can be deleted."))

    def action_confirm_insurance(self):
        """Confirm a draft insurance with a positive amount."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(self.env._(
                "Only draft insurances can be confirmed."))
        if self.amount <= 0:
            raise UserError(self.env._("Amount should be greater than zero"))
        self.state = 'confirmed'

    def action_create_invoice(self):
        """Create the next customer invoice of the insurance and open it."""
        self.ensure_one()
        self.env['account.move'].check_access('create')
        if self.state != 'confirmed':
            raise UserError(self.env._(
                "Invoices can only be created for confirmed insurances."))
        currency = self.currency_id
        remaining = self.amount_remaining
        if currency.compare_amounts(remaining, 0.0) <= 0:
            raise ValidationError(self.env._(
                "All installments have already been invoiced."))

        invoice_count = len(self._get_active_invoices())
        if self.is_fixed_payment or invoice_count + 1 >= self.policy_duration:
            # Fixed payments and the last installment settle what is left,
            # so that rounding never leaves a residue.
            price = remaining
        else:
            price = min(self.amount_installment, remaining)

        move = self.env['account.move'].with_company(self.company_id)
        invoice = move.create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.partner_id.id,
            'currency_id': currency.id,
            'invoice_user_id': self.env.user.id,
            'insurance_id': self.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [fields.Command.create({
                'name': self.env._(
                    "Insurance %(insurance)s", insurance=self.name),
                'quantity': 1,
                'price_unit': currency.round(price),
            })],
        })
        return invoice._get_records_action()

    def action_close_insurance(self):
        """Close a confirmed insurance once it is fully invoiced and paid."""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(self.env._(
                "Only confirmed insurances can be closed."))
        invoices = self._get_active_invoices()
        if not invoices:
            raise UserError(self.env._(
                "The insurance has no invoice to be closed."))
        if self.currency_id.compare_amounts(self.amount_remaining, 0.0) > 0:
            raise UserError(self.env._(
                "The insurance must be fully invoiced before closing it."))
        if any(inv.state != 'posted'
               or inv.payment_state not in ('paid', 'in_payment')
               for inv in invoices):
            raise UserError(self.env._(
                "All invoices must be paid before closing the insurance "
                "policy."))
        self.write({
            'state': 'closed',
            'close_date': fields.Date.context_today(self),
        })
