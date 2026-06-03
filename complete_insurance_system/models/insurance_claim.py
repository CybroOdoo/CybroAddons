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
from odoo import api,Command,exceptions,fields,models,_

class InsuranceClaim(models.Model):
    """
        Model representing an insurance claim.

        This model stores information related to insurance claims, such as the
        associated insurance policy, claim details, policy holder information,
        and the state of the claim. It also includes functionality for handling
        claim-related invoices and documents.
    """
    _name = 'insurance.claim'
    _description = 'Insurance Claim'
    _rec_name = 'claim_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    claim_no = fields.Char(
        string="Sequence Number",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique sequence number for identifying each claim."
    )
    insurance_id = fields.Many2one(
        comodel_name="res.insurance",
        string='Insurance Policy',
        required=True,
        tracking=True,
        help="The insurance policy associated with this claim."
    )
    policy_holder_id = fields.Many2one(
        related='insurance_id.policy_holder_id',
        string='Policy Holder',
        store=True,
        readonly=True,
        help="The policy holder of the associated insurance."
    )
    gender = fields.Selection(
        related='insurance_id.gender',
        string='Gender',
        store=True,
        readonly=True,
        help="Gender of the policy holder."
    )
    dob = fields.Date(
        related='insurance_id.dob',
        string="Date of Birth",
        store=True,
        readonly=True,
        help="Date of birth of the policy holder."
    )
    age = fields.Integer(
        related='insurance_id.age',
        string="Age",
        store=True,
        readonly=True,
        help="Age of the policy holder."
    )
    email = fields.Char(
        related='insurance_id.email',
        string="Email",
        store=True,
        readonly=True,
        help="Email of the policy holder."
    )
    phone = fields.Char(
        related='insurance_id.phone',
        string="Phone",
        store=True,
        readonly=True,
        help="Phone number of the policy holder."
    )
    policy_amount = fields.Monetary(
        string='Policy Amount',
        related="insurance_id.policy_amount",
        help="Amount covered by the insurance policy."
    )
    claim_amount = fields.Monetary(
        string='Claim Amount',
        related="insurance_policy_id.claim_amount",
        required=True,
        help="Amount claimed."
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        ondelete='restrict',
        help='The currency in which the claim amount is specified. Defaults to the company currency.'
    )
    reason_for_claim = fields.Text(
        string="Reason For Claim",
        help="Reason for filing the claim."
    )
    claim_date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        help="Date of filing the claim."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True, help="Current state of the claim.")
    agent_required = fields.Boolean(
        string="Agent Required",
        related="insurance_id.agent_required",
        store=True,
        help="Indicates if an agent is required for the policy."
    )
    agent_id = fields.Many2one(
        string="Agent",
        related="insurance_id.agent_id",
        help="Agent associated with the insurance policy."
    )
    policy_provider_id = fields.Many2one(
        string="Policy Provider",
        related="insurance_id.policy_provider_id",
        help="Provider of the insurance policy."
    )
    manager_id = fields.Many2one(
        string="Manager",
        related="insurance_id.manager_id",
        help="Manager responsible for the insurance policy."
    )
    claim_reason_id = fields.Many2one(
        string="Claim Reason",
        comodel_name="claim.reason",
        required=True,
        ondelete='restrict',
        help="Reason for filing the claim."
    )
    claim_documents_ids = fields.One2many(
        'insurance.claim.document',
        'claim_id',
        string='Claim Documents',
        help="List of documents related to the claim."
    )
    terms_condition = fields.Html(string="Terms & Conditions")
    insurance_policy_id = fields.Many2one(
        string="Insurance Policy",
        related="insurance_id.insurance_policy_id",
        help="Reference to the insurance policy."
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False,
        help="Invoice related to the claim",
        ondelete='set null'
    )
    is_invoice = fields.Boolean(
        string="Is Invoice",
        help="Indicates if an invoice is generated for the claim."
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        help="Count of invoices related to the claim."
    )

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        """Compute the number of invoices related to the claim."""
        for record in self:
            record.invoice_count = len(record.invoice_id)

    @api.model
    def create(self, vals_list):
        """Override create method to assign a unique sequence number to each insurance claim."""
        if vals_list.get('claim_no', 'New') == 'New':
            vals_list['claim_no'] = self.env['ir.sequence'].next_by_code('claim.sequence') or 'New'
        return super().create(vals_list)

    @api.onchange('insurance_policy_id')
    def _onchange_insurance_policy_id(self):
        """Update related documents based on the selected insurance policy."""
        if self.insurance_policy_id:
            claim_documents = self.insurance_policy_id.claim_document_ids
            document_lines = [Command.create({
                'document_type': doc.name,
            }) for doc in claim_documents]
            self.claim_documents_ids = document_lines

    def action_submit(self):
        """Confirm the insurance claim and check that all document types have attachments."""
        for record in self:
            missing_documents = [doc.document_type for doc in record.claim_documents_ids if
                                 not doc.document_attachment_id]
            if missing_documents:
                raise exceptions.UserError(_(
                    "The following document types are missing their attachments: %s" % ", ".join(missing_documents)
                ))
            record.state = 'submitted'

    def action_approved(self):
        """Set the claim state to 'approved'."""
        self.state = 'approved'

    def action_rejected(self):
        """Set the claim state to 'rejected'."""
        self.state = 'rejected'

    def action_claim_settlement_amount(self):
        """Create an invoice for the claim settlement amount if not already created."""
        if not self.invoice_id:
            invoice_val = self.env['account.move'].sudo().create({
                'move_type': 'in_invoice',
                'invoice_date': fields.Date.context_today(self),
                'partner_id': self.policy_holder_id.id,
                'invoice_user_id': self.env.user.id,
                'claim_id': self.id,
                'invoice_line_ids': [(fields.Command.create({
                    'name': 'Invoice For Insurance Claim',
                    'quantity': 1,
                    'price_unit': self.claim_amount,
                }))],
            })
            self.invoice_id = invoice_val

    def action_view_claim_invoice(self):
        """Open the form view of the invoice related to the claim."""
        return {
            'name': 'Claim Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.invoice_id.id
        }


class InsuranceClaimDocument(models.Model):
    """
        Represents a document related to an insurance claim.
        Each document is associated with a specific claim and includes the type of document
        and the attachment itself.
    """
    _name = "insurance.claim.document"
    _description = 'Insurance Claim Document'

    claim_id = fields.Many2one(
        'insurance.claim',
        string='Claim',
        required=True,
        ondelete='cascade',
        help="Reference to the claim."
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
