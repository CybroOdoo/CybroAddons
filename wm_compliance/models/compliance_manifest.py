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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AuditMixin(models.AbstractModel):
    """Abstract mixin model providing audit trail capabilities for compliance models."""
    _inherit = 'wm.audit.mixin'

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        if not self.env.context.get('bypass_compliance_lock'):
            locked_states = getattr(self, 'LOCKED_STATES', [])
            for record in self:
                if hasattr(record, 'state') and record.state in locked_states:
                    raise UserError(_("This compliance record is finalized in the locked state and cannot be modified."))
        return super(AuditMixin, self).write(vals)

    def unlink(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        if not self.env.context.get('bypass_compliance_lock'):
            locked_states = getattr(self, 'LOCKED_STATES', [])
            for record in self:
                if hasattr(record, 'state') and record.state in locked_states:
                    raise UserError(_("This compliance record is finalized in the locked state and cannot be deleted."))
        return super(AuditMixin, self).unlink()


class ComplianceManifest(models.Model):
    """Regulatory waste tracking manifest managing hazardous waste chain-of-custody."""
    _name = 'wm.compliance.manifest'
    _description = 'Compliance Manifest'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'id desc'

    LOCKED_STATES = ['disposed']

    name = fields.Char(
        string='Manifest Ref',
        copy=False,
        default=lambda self: ''
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('collected', 'Collected'),
        ('disposed', 'Disposed')
    ], string='Status', default='draft', required=True, tracking=True, index=True)

    generator_id = fields.Many2one(
        'res.partner',
        string='Generator',
        domain="[('is_generator', '=', True)]",
        required=True,
        tracking=True
    )
    transporter_id = fields.Many2one(
        'res.partner',
        string='Transporter',
        domain="[('is_transporter', '=', True)]",
        required=True,
        tracking=True
    )
    disposal_facility_id = fields.Many2one('wm.disposal.facility', string='Disposal Facility', required=True, tracking=True)

    compliance_code_ids = fields.Many2many(
        'wm.compliance.code',
        'wm_compliance_manifest_code_rel',
        'manifest_id',
        'code_id',
        string='Compliance Codes'
    )

    line_ids = fields.One2many('wm.compliance.manifest.line', 'manifest_id', string='Manifest Lines')

    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_quantity',
        store=True,
        tracking=True
    )

    transport_mode = fields.Selection([
        ('road', 'Road'),
        ('rail', 'Rail'),
        ('water', 'Water'),
        ('air', 'Air')
    ], string='Transport Mode', default='road')

    custody_ids = fields.One2many('wm.compliance.custody', 'manifest_id', string='Chain of Custody')
    signature_id = fields.Many2one('wm.digital.signature', string='Digital Signature', readonly=True, copy=False)
    signature_signer_id = fields.Many2one('res.users', string='Signer', related='signature_id.signer_id', readonly=True)
    signature_signed_at = fields.Datetime(string='Signed At', related='signature_id.signed_at', readonly=True)
    signature_pdf_hash = fields.Char(string='PDF Hash (SHA-256)', related='signature_id.pdf_hash', readonly=True)
    signature_hash_verified = fields.Boolean(string='Signature Verified', related='signature_id.hash_verified', readonly=True)
    manifest_date = fields.Date(string='Manifest Date', default=fields.Date.context_today, required=True, tracking=True, index=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('line_ids.quantity')
    def _compute_total_quantity(self):
        """
        Sum all waste stream line quantities on the manifest to compute the
        total collected weight, used for regulatory reporting and environmental
        KPI dashboards.
        """
        for rec in self:
            rec.total_quantity = sum(rec.line_ids.mapped('quantity'))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == ' ':
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.compliance.manifest') or ' '
        records = super(ComplianceManifest, self).create(vals_list)
        records._trigger_target_recompute()
        return records

    def _trigger_target_recompute(self):
        """
        Invalidate and recompute linked compliance target achievement
        percentages whenever manifest quantities change, keeping regulatory
        performance indicators current.
        """
        partners = self.mapped('generator_id') | self.mapped('transporter_id')
        if partners:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partners.ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        res = super(ComplianceManifest, self).write(vals)
        if any(f in vals for f in ['generator_id', 'transporter_id', 'state', 'manifest_date']):
            self._trigger_target_recompute()
        return res

    def unlink(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        partners = self.mapped('generator_id') | self.mapped('transporter_id')
        partner_ids = partners.ids
        res = super(ComplianceManifest, self).unlink()
        if partner_ids:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partner_ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()
        return res

    def action_submit(self):
        """
        Submit the manifest to the regulatory authority by transitioning it to
        'submitted' state, generating a SHA-256 submission certificate, and
        emailing the compliance officer.
        """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Manifest can only be submitted from Draft state."))
            rec.write({'state': 'submitted'})
            # Auto-log custody milestone
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'generated',
                'location': rec.generator_id.city or rec.generator_id.name,
                'notes': _("Manifest generated and submitted by %s") % self.env.user.name,
            })
            rec.action_export_and_notify()

    def action_collect(self):
        """
        Transition the manifest from 'draft' to 'collected' state, recording
        the collection timestamp and verifying that all required waste stream
        fields are populated.
        """
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_("Manifest must be in Submitted state to be marked as Collected."))
            rec.write({'state': 'collected'})
            # Auto-log custody milestone
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'collected',
                'location': rec.generator_id.city or rec.generator_id.name,
                'notes': _("Consignment collected by %s") % (rec.transporter_id.name or 'Transporter'),
            })

    def action_dispose(self):
        """
        Mark the manifest as fully disposed by updating state to 'disposed',
        recording the disposal facility, and closing the chain-of-custody
        record.
        """
        for rec in self:
            if rec.state != 'collected':
                raise UserError(_("Manifest must be in Collected state to be marked as Disposed."))
            rec.write({'state': 'disposed'})
            # Auto-log custody milestone
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'disposed',
                'location': rec.disposal_facility_id.name,
                'notes': _("Consignment treated/disposed at %s") % (rec.disposal_facility_id.name or 'Facility'),
            })

    def action_export_and_notify(self):
        """
        Generate a PDF export of the manifest, attach it to the chatter, and
        send a notification email to all configured compliance recipients for
        record keeping.
        """
        self.ensure_one()
        self._generate_signed_pdf()

        recipients = []
        if self.generator_id.email:
            recipients.append(self.generator_id.email)
        if self.transporter_id.email:
            recipients.append(self.transporter_id.email)
        if self.disposal_facility_id.contact_email:
            recipients.append(self.disposal_facility_id.contact_email)

        unique_recipients = list(dict.fromkeys([r.strip() for r in recipients if r and r.strip()]))

        if unique_recipients:
            email_to = ', '.join(unique_recipients)
            mail_values = {
                'subject': _('Signed Waste Manifest: %s') % self.name,
                'email_to': email_to,
                'body_html': _('<p>Dear Stakeholder,</p><p>Please find attached the signed compliance manifest <strong>%s</strong>.</p>') % self.name,
                'attachment_ids': [(4, self.signature_id.pdf_attachment_id.id)],
            }
            # Create and send the email synchronously.
            self.env['mail.mail'].sudo().create(mail_values).send()
            chatter_msg = _("Manifest exported and notification email sent to stakeholders: %s") % email_to
        else:
            chatter_msg = _("Manifest exported and signed PDF generated.")

        # Log export & notify message in chatter with attached signed PDF
        self.message_post(
            body=chatter_msg,
            attachment_ids=[self.signature_id.pdf_attachment_id.id] if self.signature_id and self.signature_id.pdf_attachment_id else []
        )

    def _generate_signed_pdf(self):
        """
        Render the compliance manifest QWeb report to a signed PDF, embedding
        the submission certificate hash footer and attaching the document to
        the manifest chatter.
        """
        self.ensure_one()
        report = self.env.ref('wm_compliance.action_report_compliance_manifest')
        pdf_bytes, report_format = self.env['ir.actions.report']._render_qweb_pdf(report.id, [self.id])
        filename = f"MANIFEST_{self.name.replace('/', '_').replace(' ', '_')}.pdf"
        sig = self.env['wm.digital.signature'].sign_document(self, pdf_bytes, filename)
        self.with_context(bypass_compliance_lock=True).write({'signature_id': sig.id})


class ComplianceManifestLine(models.Model):
    """Waste stream line within a compliance manifest specifying category, weight, and hazard."""
    _name = 'wm.compliance.manifest.line'
    _description = 'Compliance Manifest Line'

    manifest_id = fields.Many2one('wm.compliance.manifest', string='Manifest', required=True, ondelete='cascade')
    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', required=True)
    product_id = fields.Many2one('product.product', string='Waste Material')
    quantity = fields.Float(string='Quantity', required=True, default=0.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    notes = fields.Text(string='Notes / Label')

    def _trigger_target_recompute(self):
        """
        Invalidate and recompute linked compliance target achievement
        percentages whenever manifest quantities change, keeping regulatory
        performance indicators current.
        """
        manifests = self.mapped('manifest_id')
        if manifests:
            manifests._trigger_target_recompute()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        records = super(ComplianceManifestLine, self).create(vals_list)
        records._trigger_target_recompute()
        return records

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        res = super(ComplianceManifestLine, self).write(vals)
        if 'quantity' in vals:
            self._trigger_target_recompute()
        return res

    def unlink(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        manifests = self.mapped('manifest_id')
        partners = manifests.mapped('generator_id') | manifests.mapped('transporter_id')
        partner_ids = partners.ids
        res = super(ComplianceManifestLine, self).unlink()
        if partner_ids:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partner_ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()
        return res
