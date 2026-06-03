# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, Command, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResInsurance(models.Model):
    """Model representing an Insurance Policy.

        This model manages all the details associated with an insurance policy,
        including the policy holder, policy details, commission structure, and invoices.
        """
    _name = 'res.insurance'
    _rec_name = 'insurance_no'
    _description = 'Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    insurance_no = fields.Char(
        string="Sequence Number",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique sequence number for identifying each insurance."
    )
    policy_holder_id = fields.Many2one(
        comodel_name="res.partner",
        string='Policy Holder',
        domain=[('agent', '=', False)],
        required=True,
        tracking=True,
        ondelete='cascade',
        help="The policy holder of the insurance."
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', required=True, help="Gender of the policy holder.",
        tracking=True)
    dob = fields.Date(string="Date of Birth",
                      help="Date of birth of the policy holder.")
    age = fields.Integer(string="Age", compute="_compute_age", readonly=True,
                         help="Age of the policy holder.")
    email = fields.Char(
        string="Email",
        related='policy_holder_id.email',
        readonly=False,
        help="Email of the policy holder."
    )
    phone = fields.Char(
        string="Phone",
        related='policy_holder_id.phone',
        readonly=False,
        help="Phone number of the policy holder."
    )
    insurance_policy_id = fields.Many2one(
        string="Insurance Policy",
        comodel_name="insurance.policy",
        tracking=True,
        ondelete='restrict',
        help="Reference to the insurance policy."
    )
    policy_category_id = fields.Many2one(
        string="Policy Category",
        related="insurance_policy_id.policy_category_id",
        help="Category of the insurance policy."
    )
    insurance_for_id = fields.Many2one(
        string="Insurance For",
        comodel_name="insurance.for",
        ondelete='set null',
        help="Entity for whom the insurance is taken."
    )
    policy_provider_id = fields.Many2one(
        string="Policy Provider",
        comodel_name="res.company",
        ondelete='restrict',
        help="Provider of the insurance policy."
    )
    issue_date = fields.Date(string='Issue Date',
                             help="Issue date of the insurance policy.")
    expiry_date = fields.Date(string='Expiry Date',
                              help="Expiry date of the insurance policy.")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        ondelete='restrict',
        help='The currency in which the premium is calculated. Defaults to the company currency.'
    )
    policy_amount = fields.Monetary(
        string='Policy Amount',
        related="insurance_policy_id.insurance_amount",
        help="Amount covered by the insurance policy."
    )
    manager_id = fields.Many2one(
        string="Manager",
        comodel_name="res.users",
        ondelete='set null',
        help="Manager responsible for the insurance policy."
    )
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
        ('running', 'Running'),
        ('expired', 'Expired')
    ], string='State',
        default='new',
        copy=False,
        tracking=True,
        help="Current state of the insurance policy.")
    policy_description = fields.Html(
        string='Policy Description',
        related="insurance_policy_id.policy_description",
        help='Detailed description of the insurance policy.'
    )
    terms_condition = fields.Html(
        string='Terms and Conditions',
        related="insurance_policy_id.terms_condition",
        help='Terms and conditions associated with the insurance policy.'
    )
    insurance_nominee_line_ids = fields.One2many(
        string="Insurance Nominee",
        comodel_name="insurance.nominee.details",
        inverse_name="nominee_detail_id",
        help="List of nominees for the insurance policy."
    )
    agent_required = fields.Boolean(
        string="Agent Required",
        store=True,
        help="Indicates if an agent is required for the policy."
    )
    agent_id = fields.Many2one(
        string="Agent",
        comodel_name="res.partner",
        domain="[('agent', '=', True)]",
        ondelete='set null',
        help="Agent associated with the insurance policy."
    )
    agent_phone = fields.Char(
        string="Phone",
        related="agent_id.phone",
        help="Phone number of the agent."
    )
    commission_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
    ], required=True, default='fixed', help="Type of commission for the agent.",
        tracking=True)
    fixed_amount = fields.Monetary(
        string="Fixed Amount",
        help="Fixed commission amount for the agent."
    )
    commission_percentage = fields.Integer(string="Commission(%)",
                                           help="Percentage commission for the agent.")
    percentage_amount = fields.Monetary(string="Commission Amount",
                                        compute="_compute_commission_amount")
    payment_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('installment', 'Installment'),
    ], required=True, default='fixed', help="Type of payment for the policy.",
        tracking=True)
    total_policy_amount = fields.Monetary(
        string="Total Policy Amount",
        related="insurance_policy_id.insurance_amount",
        help="Total amount of the insurance policy."
    )
    document_ids = fields.One2many(
        'insurance.document',
        'insurance_id',
        string='Related Documents',
        help="List of documents related to the insurance policy."
    )
    commission_invoice_id = fields.Many2one(
        comodel_name='account.move',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="Invoice related to the commission."
    )
    fixed_invoice_id = fields.Many2one(
        comodel_name='account.move',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="Invoice related to the fixed insurance."
    )
    is_invoice = fields.Boolean(help="Indicates whether an invoice exists.")
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        help="Count of invoices related to the insurance policy."
    )
    insurance_fixed_invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_insurance_fixed_invoice_count',
        help="Count of fixed invoices related to the insurance policy."
    )
    invoice_ids = fields.One2many(
        'account.move', 'insurance_id',
        readonly=True,
        copy=False,
        help="Invoices related to insurance."
    )
    policy_duration = fields.Integer(
        string='Duration in months',
        help="Specify the policy duration in months."
    )
    amount_installment = fields.Monetary(
        string="Installment Amount",
        compute="_compute_installment_amount",
        required=True,
        help="Installment amount for the policy."
    )
    amount_remaining = fields.Monetary(
        string='Amount remaining',
        compute='_compute_amount_remaining',
        help="Remaining amount to be paid for the policy."
    )

    @api.depends('dob')
    def _compute_age(self):
        """Calculate the age of the policy holder based on their date of birth."""
        today = fields.Date.today()
        for record in self:
            if record.dob:
                delta = today - record.dob
                record.age = delta.days // 365
                if record.age < 0:
                    raise ValidationError('Invalid Date Of Birth')
            else:
                record.age = 0  # Default to 0 if dob is not set

    def count_genders(self):
        male_count = self.search_count([('gender', '=', 'male')])
        female_count = self.search_count([('gender', '=', 'female')])
        products = ['Male', 'Female', ]
        counts = [male_count, female_count, ]
        result = {'products': products, 'count': counts}
        return result

    def insurance_policy_count(self):
        """
            Counts the number of 'res.insurance' records associated with each insurance policy.

            This method fetches all insurance policies from the 'insurance.policy' model,
            iterates over each policy, and counts the related 'res.insurance' records.
            It returns a dictionary containing the names of the policies and their corresponding counts.
        """
        # Fetch all insurance policies
        insurance_policies = self.env['insurance.policy'].search([])

        # Initialize lists to store policy names and counts
        policy_names = []
        policy_counts = []

        # Iterate over each insurance policy
        for policy in insurance_policies:
            # Count the number of res.insurance records associated with the current policy
            count = self.env['res.insurance'].search_count(
                [('insurance_policy_id', '=', policy.id)])

            # Add the policy name and count to the respective lists
            policy_names.append(policy.insurance_policy_id.name)
            policy_counts.append(count)

        # Create the result dictionary
        result = {
            'products': policy_names,
            'count': policy_counts
        }

        return result

    @api.depends('total_policy_amount', 'policy_duration')
    def _compute_installment_amount(self):
        """Compute the installment amount based on total policy amount and policy duration.

               The installment amount is calculated as the total policy amount divided by the policy duration.
               If the policy duration is zero, the installment amount is set to 0.0.
               """
        for record in self:
            if record.policy_duration != 0:
                record.amount_installment = (
                        record.total_policy_amount / record.policy_duration)
            else:
                record.amount_installment = 0.0

    @api.depends('total_policy_amount', 'amount_installment',
                 'invoice_ids.amount_total')
    def _compute_amount_remaining(self):
        """Compute the remaining amount based on total policy amount and total invoices.

                The remaining amount is calculated as the total policy amount minus the sum of all invoice amounts.
                """
        for record in self:
            total_invoice_amount = sum(
                record.invoice_ids.mapped('amount_total'))
            total_amount = record.total_policy_amount
            record.amount_remaining = total_amount - total_invoice_amount

    def action_create_installment_invoice(self):
        """Create an invoice for the installment payment.

                If the remaining amount is less than or equal to zero, a validation error is raised.
                If the policy duration is not set, a validation error is raised.
                The state of the record is set to 'running', and a new invoice is created.
                The invoice is linked to the corresponding partner and insurance line.
                """
        if self.amount_remaining <= 0:
            raise ValidationError(
                _('Installment is completed,No need to create invoice again'))
        else:
            if not self.policy_duration:
                raise ValidationError(
                    _('Please add the policy Duration'))
            self.state = 'running'
            created_invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(self),
                'partner_id': self.policy_holder_id.id,
                'invoice_user_id': self.env.user.id,
                'invoice_line_ids': [(fields.Command.create({
                    'name': 'Invoice For Installment Insurance',
                    'quantity': 1,
                    'price_unit': self.total_policy_amount if self.payment_type == 'fixed' else
                    self.amount_installment
                }))],
            })
            self.write({'invoice_ids': [Command.link(created_invoice.id)]})
            self.env['res.partner'].sudo().browse(
                self.policy_holder_id.id).write({
                'insurance_line_ids': [Command.create({
                    'insurance_id': self.insurance_no,
                    'policy_holder_id': self.policy_holder_id.id,
                    'policy_category_id': self.policy_category_id.id,
                    'issue_date': self.issue_date,
                    'expiry_date': self.expiry_date,
                    'commission_bill_id': created_invoice.name,
                })]
            })

    @api.depends('fixed_invoice_id')
    def _compute_insurance_fixed_invoice_count(self):
        """Compute the count of fixed invoices associated with the insurance record.

                The count is determined by the length of the fixed_invoice_id relation.
                """
        for record in self:
            record.insurance_fixed_invoice_count = len(record.fixed_invoice_id)

    def action_confirm_policy(self):
        """Confirm the insurance policy and check that all document types have attachments."""
        for record in self:
            missing_documents = [doc.document_type for doc in
                                 record.document_ids if
                                 not doc.document_attachment_id]
            if missing_documents:
                raise exceptions.UserError(_(
                    "The following document types are missing their attachments: %s" % ", ".join(
                        missing_documents)
                ))
            record.state = 'confirmed'
            record.issue_date = fields.Date.context_today(self)

    @api.depends('policy_amount', 'commission_percentage')
    def _compute_commission_amount(self):
        """Compute the commission amount based on the policy amount and commission percentage."""
        for record in self:
            if record.commission_percentage:
                record.percentage_amount = record.policy_amount * (
                        record.commission_percentage / 100)
            else:
                record.percentage_amount = record.policy_amount

    @api.depends('commission_invoice_id')
    def _compute_invoice_count(self):
        """Compute the count of invoices related to the insurance policy."""
        for record in self:
            record.invoice_count = len(record.commission_invoice_id)

    @api.onchange('insurance_policy_id')
    def _onchange_insurance_policy_id(self):
        """Update related documents based on the selected insurance policy."""
        self.document_ids = [Command.clear()]
        if self.insurance_policy_id:
            policy_documents = self.insurance_policy_id.policy_document_ids
            document_lines = [Command.create({
                'document_type': doc.name,
            }) for doc in policy_documents]
            self.document_ids = document_lines

    @api.model
    def create(self, vals_list):
        """Override create method to assign a unique sequence number to each insurance policy."""
        if vals_list.get('insurance_no', 'New') == 'New':
            vals_list['insurance_no'] = self.env['ir.sequence'].next_by_code(
                'insurance.sequence') or 'New'
        return super().create(vals_list)

    def action_create_claim(self):
        """
            Opens a form view to create a new insurance claim.

            This method returns an action that opens the 'insurance.claim' model in a
            form view, allowing the user to create a new claim. The context is set
            with the current record's ID as the default insurance ID.

            """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Claim',
            'res_model': 'insurance.claim',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_insurance_id': self.id,
            },
            'target': 'new'
        }

    def action_insurance_expired(self):
        """
            Marks the insurance policy as expired if all related invoices are paid.

            This method checks the state of all related invoices. If any invoice is
            found to be unpaid, it raises a UserError. If all invoices are paid,
            it updates the state of the insurance policy to 'expired' and sets the
            expiry date to the current date.

            """
        for records in self.invoice_ids:
            if records.state == 'paid':
                raise UserError(_("All invoices must be paid"))
        self.state = 'expired'
        self.expiry_date = fields.Date.context_today(self)

    def action_commission_invoice(self):
        """Create an invoice for the agent's commission."""
        if not self.agent_id:
            raise exceptions.UserError(
                _("Agent is required to create an invoice."))
        created_invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.agent_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_line_ids': [Command.create({
                'name': 'Invoice For Commission',
                'quantity': 1,
                'price_unit': self.fixed_amount if self.commission_type == 'fixed' else self.percentage_amount
            })],
        })
        self.commission_invoice_id = created_invoice.id
        self.is_invoice = True
        self.env['res.partner'].sudo().browse(self.agent_id.id).write({
            'insurance_line_ids': [Command.create({
                'insurance_id': self.insurance_no,
                'policy_holder_id': self.policy_holder_id.id,
                'policy_category_id': self.policy_category_id.id,
                'issue_date': self.issue_date,
                'expiry_date': self.expiry_date,
                'commission_bill_id': created_invoice.name,
            })]
        })
        return {
            'name': 'Commission Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': created_invoice.id
        }

    def action_create_fixed_invoice(self):
        """
            Creates a fixed invoice for the insurance policy and updates the related partner's insurance lines.

            This method sets the state of the policy to 'running', creates a new invoice in the
            'account.move' model, and associates it with the policy holder. It also updates the
            related partner with the new insurance line information.
            """
        self.state = 'running'
        fixed_invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.policy_holder_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_line_ids': [Command.create({
                'name': 'Invoice For Fixed Insurance',
                'quantity': 1,
                'price_unit': self.total_policy_amount
            })],
        })
        self.fixed_invoice_id = fixed_invoice.id
        self.is_invoice = True
        self.env['res.partner'].sudo().browse(self.policy_holder_id.id).write({
            'insurance_line_ids': [Command.create({
                'insurance_id': self.insurance_no,
                'policy_holder_id': self.policy_holder_id.id,
                'policy_category_id': self.policy_category_id.id,
                'issue_date': self.issue_date,
                'expiry_date': self.expiry_date,
                'commission_bill_id': fixed_invoice.name,
            })]
        })
        return {
            'name': 'Invoice For Fixed Insurance',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': fixed_invoice.id
        }

    def action_view_fixed_invoice(self):
        """
            Opens the fixed insurance invoice in a form view.

            This method returns an action that opens the invoice associated with the current policy
            in a form view.
            """
        return {
            'name': 'Fixed insurance Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.fixed_invoice_id.id
        }

    def action_view_commission_invoice(self):
        """View the created commission invoice."""
        return {
            'name': 'Commission Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.commission_invoice_id.id
        }

    @api.model
    def get_dashboard_data(self):
        """ Return the dashboard data"""
        total_insurance = self.env['res.insurance'].search_count([])
        new_insurance = self.env['res.insurance'].search_count(
            [('state', '=', 'new')])
        running_insurance = self.env['res.insurance'].search_count(
            [('state', '=', 'running')])
        expired_insurance = self.env['res.insurance'].search_count(
            [('state', '=', 'expired')])
        total_claim = self.env['insurance.claim'].search_count([])
        submit_claim = self.env['insurance.claim'].search_count(
            [('state', '=', 'submitted')])
        approve_claim = self.env['insurance.claim'].search_count(
            [('state', '=', 'approved')])
        reject_claim = self.env['insurance.claim'].search_count(
            [('state', '=', 'rejected')])
        agent_count = self.env['res.partner'].search_count(
            [('agent', '=', True)])
        categories_count = self.env['insurance.policy.category'].search_count(
            [])
        sub_categories_count = self.env[
            'insurance.policy.sub.category'].search_count([])
        insurance_policy = self.env['insurance.policy'].search_count([])
        return {
            'total_insurance': total_insurance,
            'new_insurance': new_insurance,
            'running_insurance': running_insurance,
            'expired_insurance': expired_insurance,
            'total_claim': total_claim,
            'submitted_claim': submit_claim,
            'approved_claim': approve_claim,
            'rejected_claim': reject_claim,
            'agent_count': agent_count,
            'categories_count': categories_count,
            'sub_categories_count': sub_categories_count,
            'insurance_policy': insurance_policy,
        }


class InsuranceNomineeDetails(models.Model):
    """
        Model to store the details of nominees associated with insurance policies.

        This model keeps track of nominee information such as name, relation with the policy holder,
        date of birth, age, and the percentage of the insurance amount allocated to each nominee.
        """
    _name = "insurance.nominee.details"
    _description = "Insurance Nominee Details"

    nominee_id = fields.Many2one(
        string="Name",
        comodel_name="res.partner",
        ondelete='cascade',
        help="Nominee's name."
    )
    relation_with_policy_holder_id = fields.Many2one(
        comodel_name="nominee.relation",
        string="Relation With Policy Holder",
        help="Relation of the nominee with the policy holder."
    )
    dob = fields.Date(string="Date Of Birth",
                      help="Date of birth of the nominee.")
    age = fields.Integer(string="Age", readonly=True, compute="_compute_age",
                         help="Age of the nominee.")
    percentage = fields.Integer(
        string="Percentage",
        help="Percentage of the insurance amount allocated to the nominee."
    )
    nominee_detail_id = fields.Many2one(
        comodel_name="res.insurance",
        ondelete='cascade',
        help="Reference to the insurance policy."
    )

    @api.depends('dob')
    def _compute_age(self):
        """
                Compute the age of the nominee based on their date of birth.

                This method calculates the age of the nominee from the date of birth field (dob)
                and updates the 'age' field accordingly. If the date of birth is not set,
                the age will be set to zero.

                The computation is triggered whenever the date of birth changes.
                """
        for record in self:
            if record.dob:
                today = fields.Date.today()
                born = record.dob
                # Calculate the age based on the current date and dob
                record.age = today.year - born.year - (
                        (today.month, today.day) < (born.month, born.day))
            else:
                record.age = 0


class InsuranceDocument(models.Model):
    """
    Model to represent insurance documents associated with an insurance policy.
    """
    _name = "insurance.document"
    _description = 'Insurance Document'

    insurance_id = fields.Many2one(
        'res.insurance',
        string='Insurance Policy',
        required=True,
        ondelete='cascade',
        help="Reference to the insurance policy."
    )
    document_type = fields.Char(
        string='Document Type',
        required=True,
        help="Type of the document."
    )
    document_attachment_id = fields.Binary(
        string='Document',
        required=True,
        copy=False,
        help="Attachment of the document."
    )
