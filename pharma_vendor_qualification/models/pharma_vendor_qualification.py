# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
import uuid


class PharmaVendorQualification(models.Model):
    """Vendor Qualification — status, audit scores, and validity dates for pharma vendors."""
    _name = 'pharma.vendor.qualification'
    _description = 'Vendor Qualification'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _rec_name = 'display_name'
    _order = 'audit_date desc, id desc'

    name = fields.Char(
        string='Qualification Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Auto-generated unique qualification reference number (e.g. VQ/2026/00001).'
    )

    version = fields.Integer(
        string='Version',
        default=1,
        required=True,
        readonly=True,
        tracking=True,
        help='Auto-increments each time a vendor qualification is revised or reset to draft.'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Uncheck to archive the vendor qualification record.'
    )

    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Vendor going through the qualification process.'
    )

    product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products',
        domain=[('tracking', '=', 'lot')],
        required=True,
        tracking=True,
        help='Products they are being qualified to supply.'
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('questionnaire_sent', 'Questionnaire Sent'),
            ('documents_received', 'Documents Received'),
            ('audit_scheduled', 'Audit Scheduled'),
            ('rejected', 'Rejected'),
            ('not_qualified', 'Not Qualified'),
            ('approved', 'Approved'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Tracks where the vendor is in the qualification journey.'
    )

    audit_date = fields.Date(
        string='Audit Date',
        tracking=True,
        help='Date the physical or remote audit was conducted.'
    )

    total_score = fields.Float(
        string='Total Score',
        required=True,
        tracking=True,
        help='Maximum possible score for the audit (limited to 100). Note: If the '
             'Audit Score is below the approval percentage configured in the '
             'Pharmaceutical ERP settings, the vendor will automatically be '
             'marked as Not Qualified.'
    )

    audit_score = fields.Float(
        string='Audit Score',
        tracking=True,
        help='Score given to the vendor after the audit. Must reach the approval '
             'percentage of the Total Score configured in the settings to be approved.'
    )

    def _is_audit_score_passing(self):
        """Return True when the audit score meets the configured approval percentage."""
        self.ensure_one()
        if self.audit_score <= 0.0:
            return False
        percentage = self.env.company.pharma_vendor_approval_percentage
        return self.audit_score >= self.total_score * percentage / 100.0

    @api.constrains('audit_score', 'total_score')
    def _check_audit_score_validity(self):
        """Executes the _check_audit_score_validity operation."""
        for rec in self:
            if rec.total_score <= 0.0:
                raise UserError(_("You must provide a Total Score greater than 0 before saving."))
            if rec.total_score > 100.0:
                raise UserError(_("The Total Score cannot be greater than 100."))
            if rec.total_score > 0 and rec.audit_score > rec.total_score:
                raise UserError(_("The actual audit score cannot be greater than the total score."))

    gmp_certificate = fields.Binary(
        string='GMP Certificate',
        attachment=True,
        help="Vendor's GMP certificate uploaded as a file."
    )

    gmp_certificate_filename = fields.Char(
        string='GMP Certificate Filename',
        help='Original filename of the uploaded GMP certificate.'
    )

    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        readonly=True,
        tracking=True,
        help='QA person who gave final approval.'
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Reason recorded if the vendor was rejected.'
    )

    avl_ids = fields.Many2many(
        comodel_name='pharma.avl',
        string='AVL Entries',
        readonly=True,
        help='AVL entries auto-created when vendor is approved.'
    )

    template_id = fields.Many2one(
        comodel_name='pharma.questionnaire.template',
        string='Questionnaire Template',
        tracking=True,
        help='Select a template to auto-populate the questionnaire.'
    )

    response_ids = fields.One2many(
        comodel_name='pharma.vendor.qualification.response',
        inverse_name='qualification_id',
        string='Responses',
        copy=True,
            help='Specifies the Responses for this record.',
    )

    access_token = fields.Char(
        string='Access Token',
        copy=False,
        help='Specifies the Access Token for this record.',
    )
    submission_date = fields.Datetime(
        string='Submission Date',
        readonly=True,
        copy=False,
        help='Date and time when the vendor submitted the questionnaire via the portal.'
    )

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Auto-populates the questionnaire responses based on the selected template's questions."""
        if self.template_id:
            # Clear existing responses
            self.response_ids = [(5, 0, 0)]
            # Auto-populate based on template questions
            lines = []
            for question in self.template_id.question_ids:
                lines.append((0, 0, {
                    'question_id': question.id,
                }))
            self.response_ids = lines

    @api.onchange('audit_score', 'total_score')
    def _onchange_audit_score(self):
        """Executes the _onchange_audit_score operation."""
        if self.status == 'audit_scheduled' and not self._is_audit_score_passing():
            self.status = 'not_qualified'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
            help='Specifies the Display Name for this record.',
    )

    @api.depends('name', 'vendor_id')
    def _compute_display_name(self):
        """Generates display name with sequence reference and vendor name."""
        for record in self:
            vendor = record.vendor_id.name or _('New')
            ref = record.name or _('QUAL')
            record.display_name = f"{ref} - {vendor}"

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to auto-generate sequence reference and AVL records."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.vendor.qualification') or _('New')
        records = super().create(vals_list)
        for rec in records:
            if rec.status == 'approved':
                rec.with_context(skip_avl_trigger=True)._create_or_update_avl()
        return records

    def write(self, vals):
        """Overrides write to synchronize changes to the corresponding AVL records."""
        if 'audit_score' in vals:
            # Audit score records the vendor's actual result and may only be entered
            # once the audit has been scheduled (after the "Schedule Audit" button is
            # clicked), while in the 'Audit Scheduled' state and awaiting the decision.
            blocked = self.filtered(lambda r: r.status != 'audit_scheduled')
            if blocked:
                raise UserError(_(
                    "The Audit Score can only be entered after the audit has been "
                    "scheduled, while the qualification is in the 'Audit Scheduled' state."
                ))
        if 'total_score' in vals:
            # Total score defines the audit's maximum and must be fixed before the
            # audit is scheduled; it locks once the "Schedule Audit" button is clicked.
            blocked = self.filtered(
                lambda r: r.status not in ('draft', 'questionnaire_sent', 'documents_received'))
            if blocked:
                raise UserError(_(
                    "The Total Score can only be changed before the audit is scheduled "
                    "(Draft, Questionnaire Sent or Documents Received)."
                ))
        res = super().write(vals)
        # Auto-disqualify only when an audit score is actually being entered.
        # (Without this guard, merely scheduling the audit — when the score is
        # still 0 — would instantly flip the record to Not Qualified.)
        if 'audit_score' in vals:
            for rec in self:
                if rec.status == 'audit_scheduled' and not rec._is_audit_score_passing():
                    rec.write({'status': 'not_qualified'})
        if self.env.context.get('skip_avl_trigger'):
            return res
        trigger_fields = {'status', 'audit_date', 'approved_by', 'vendor_id', 'product_ids'}
        if trigger_fields.intersection(vals.keys()):
            for rec in self:
                if rec.status == 'approved':
                    rec.with_context(skip_avl_trigger=True)._create_or_update_avl()
        return res

    def _create_or_update_avl(self):
        """Create or update AVL entries for this vendor/products combination."""
        self.ensure_one()
        if not self.vendor_id or not self.product_ids:
            return

        avl_list = self.env['pharma.avl']
        for prod in self.product_ids:
            avl = self.env['pharma.avl'].search([
                ('vendor_id', '=', self.vendor_id.id),
                ('product_id', '=', prod.id)
            ], limit=1)

            vals = {
                'vendor_id': self.vendor_id.id,
                'product_id': prod.id,
                'status': 'approved',
                'approval_date': self.audit_date or fields.Date.context_today(self),
                'approved_by': self.approved_by.id or self.env.uid,
            }

            if avl:
                avl.write(vals)
            else:
                # AVL entry is a downstream artefact of qualifying the vendor;
                # QA has no create right, so it is created elevated.
                avl = self.env['pharma.avl'].sudo().create(vals)
            avl_list |= avl

        self.write({'avl_ids': [(6, 0, avl_list.ids)]})

    def action_send_questionnaire(self):
        """Email the vendor a secure link to the portal questionnaire."""
        for rec in self:
            if rec.status == 'draft':
                if not rec.template_id:
                    raise UserError(_("Please select a Questionnaire Template before sending."))
                if not rec.vendor_id.email:
                    raise UserError(_("The selected vendor does not have an email address configured."))

                # Generate responses to ensure they match the template perfectly at send time.
                # Response lines are regenerated (create/delete) as part of sending;
                # QA has no create/unlink right, so this runs elevated.
                commands = [(5, 0, 0)]
                for question in rec.template_id.question_ids:
                    commands.append((0, 0, {'question_id': question.id}))
                rec.sudo().write({'response_ids': commands})

                # Ensure access token
                if not rec.access_token:
                    rec.access_token = uuid.uuid4().hex

                # Send Email
                template = self.env.ref('pharma_vendor_qualification.email_template_vendor_questionnaire')
                if template:
                    template.send_mail(rec.id, force_send=True)

                # Log chatter
                rec.message_post(body=_("Questionnaire sent to %s", rec.vendor_id.email))

                # Update Status
                rec.status = 'questionnaire_sent'

    def action_receive_documents(self):
        """Transition the qualification to Documents Received."""
        for rec in self:
            if rec.status == 'questionnaire_sent':
                rec.status = 'documents_received'

    def action_schedule_audit(self):
        """Transition the qualification to Audit Scheduled with an audit date set."""
        for rec in self:
            if rec.status == 'documents_received':
                if not rec.audit_date:
                    raise UserError(_("Please specify an Audit Date before scheduling the audit."))
                if rec.audit_date < fields.Date.today():
                    raise UserError(_("The Audit Date cannot be in the past."))
                rec.status = 'audit_scheduled'

    def action_approve(self):
        """Mark the qualification Approved and set the current user as approver."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can approve a vendor qualification.'),
        )
        for rec in self:
            if rec.status == 'audit_scheduled':
                if not rec._is_audit_score_passing():
                    if self.env.context.get('confirm_not_qualified'):
                        rec.write({
                            'status': 'not_qualified',
                            'audit_date': rec.audit_date or fields.Date.context_today(self),
                        })
                    else:
                        return {
                            'name': _('Confirmation Required'),
                            'type': 'ir.actions.act_window',
                            'res_model': 'pharma.vendor.qualification.confirm.wizard',
                            'view_mode': 'form',
                            'target': 'new',
                            'context': {
                                'default_qualification_id': rec.id,
                                'default_message': _('Audit score is below required score. Mark vendor as Not Qualified?'),
                            }
                        }
                else:
                    rec.write({
                        'status': 'approved',
                        'approved_by': self.env.user.id,
                        'audit_date': rec.audit_date or fields.Date.context_today(self),
                    })

    def action_reject(self):
        """Marks the vendor qualification as 'Rejected'."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reject a vendor qualification.'),
        )
        for rec in self:
            if rec.status == 'audit_scheduled':
                rec.status = 'rejected'

    def action_reset_draft(self):
        """Archives the existing qualification and creates a new active draft copy to restart the process."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reset a vendor qualification to draft.'),
        )
        new_quals = self.env['pharma.vendor.qualification']
        for rec in self:
            old_ver = rec.version
            rec.write({'active': False})
            new_qual = rec.copy({
                'name': rec.name,
                'active': True,
                'status': 'draft',
                'version': old_ver + 1,
                'audit_date': False,
                'audit_score': 0.0,
                'approved_by': False,
                'rejection_reason': False,
                'access_token': False,
                'submission_date': False,
            })
            new_quals |= new_qual

        if len(new_quals) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pharma.vendor.qualification',
                'res_id': new_quals.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.vendor.qualification',
            'view_mode': 'list,form',
            'domain': [('id', 'in', new_quals.ids)],
            'target': 'current',
        }
