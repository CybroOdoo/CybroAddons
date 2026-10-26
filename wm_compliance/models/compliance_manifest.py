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
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class AuditMixin(models.AbstractModel):
    """Abstract mixin model providing audit trail capabilities for compliance models."""
    _inherit = 'wm.audit.mixin'

    def _compliance_lock_bypassed(self):
        """The lock bypass is honoured only for superuser (sudo) calls made by
        trusted server code; a ``bypass_compliance_lock`` key sent in an RPC
        context by a normal user is ignored."""
        return bool(self.env.su and self.env.context.get('bypass_compliance_lock'))

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        if not self._compliance_lock_bypassed():
            locked_states = getattr(self, 'LOCKED_STATES', [])
            for record in self:
                if hasattr(record, 'state') and record.state in locked_states:
                    raise UserError(_("This compliance record is finalized in the locked state and cannot be modified."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_record(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        if not self._compliance_lock_bypassed():
            locked_states = getattr(self, 'LOCKED_STATES', [])
            for record in self:
                if hasattr(record, 'state') and record.state in locked_states:
                    raise UserError(_("This compliance record is finalized in the locked state and cannot be deleted."))


class ComplianceManifest(models.Model):
    """Regulatory waste tracking manifest managing hazardous waste chain-of-custody."""
    _name = 'wm.compliance.manifest'
    _description = 'Compliance Manifest'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'id desc'

    LOCKED_STATES = ['disposed']
    # Regulatory content frozen once the manifest leaves draft; state,
    # signature and chatter stay writable for the workflow.
    LOCKED_AFTER_SUBMIT_FIELDS = (
        'generator_id', 'transporter_id', 'disposal_facility_id',
        'compliance_code_ids', 'line_ids', 'manifest_date', 'company_id',
    )

    name = fields.Char(
        string='Manifest Ref',
        copy=False,
        default=lambda self: ''
    )

    notified_at = fields.Datetime(
        string='Exported & Notified On', readonly=True, copy=False,
        help='Set when the signed manifest was exported and stakeholders were emailed.')

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

    @api.depends('line_ids.quantity', 'line_ids.uom_id')
    def _compute_total_quantity(self):
        """
        Sum all waste stream line quantities on the manifest to compute the
        total collected weight, used for regulatory reporting and environmental
        KPI dashboards. Lines are normalised to kg where their UoM allows it.
        """
        for rec in self:
            rec.total_quantity = rec.line_ids._get_total_quantity_kg()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == ' ':
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.compliance.manifest') or ' '
        # Lines given inline belong to the manifest being created: allow them
        # even when the manifest is created directly in a non-draft state.
        records = super(ComplianceManifest, self.with_context(
            wm_manifest_creating=True)).create(vals_list).with_env(self.env)
        records._trigger_target_recompute()
        return records

    def _trigger_target_recompute(self, old_partners=None):
        """
        Invalidate and recompute linked compliance target achievement
        percentages whenever manifest quantities change, keeping regulatory
        performance indicators current.
        """
        partners = self.mapped('generator_id') | self.mapped('transporter_id')
        if old_partners:
            partners |= old_partners
        if partners:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partners.ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        if not self.env.su:
            if 'state' in vals:
                raise UserError(_("The manifest status can only be changed with the Submit, Collect and Dispose buttons."))
            locked_fields = [f for f in self.LOCKED_AFTER_SUBMIT_FIELDS if f in vals]
            if locked_fields and any(rec.state != 'draft' for rec in self):
                raise UserError(_(
                    "Submitted manifests cannot be modified (%s). Only draft manifests can be edited."
                ) % ', '.join(self._fields[f].string for f in locked_fields))
        old_partners = None
        if any(f in vals for f in ['generator_id', 'transporter_id']):
            old_partners = self.mapped('generator_id') | self.mapped('transporter_id')
        res = super().write(vals)
        if any(f in vals for f in ['generator_id', 'transporter_id', 'state', 'manifest_date']):
            self._trigger_target_recompute(old_partners=old_partners)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_submitted_manifest(self):
        """Only draft manifests can be deleted."""
        if not self._compliance_lock_bypassed():
            for record in self:
                if record.state != 'draft':
                    raise UserError(_(
                        "Manifest '%s' has been submitted and cannot be deleted. "
                        "Only draft manifests can be deleted.") % record.display_name)

    def unlink(self):
        """Refresh the compliance targets of the affected partners."""
        partners = self.mapped('generator_id') | self.mapped('transporter_id')
        partner_ids = partners.ids
        res = super().unlink()
        if partner_ids:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partner_ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()
        return res

    def _get_manifest_type(self):
        """Derive the manifest stream type from the attached compliance codes.

        Returns the type only when the typed codes agree on a single one,
        otherwise False (meaning: match rules of any manifest type).
        """
        self.ensure_one()
        types = set(self.compliance_code_ids.mapped('manifest_type')) - {False}
        return types.pop() if len(types) == 1 else False

    @api.onchange('generator_id', 'line_ids')
    def _onchange_suggest_compliance_codes(self):
        """
        Suggest compliance codes and manifest requirements based on generator location and waste categories.
        """
        if not self.generator_id:
            return None
        point = getattr(self.generator_id, 'collection_point_ids', False)
        point_rec = point[0] if point else False
        c_state = point_rec.state_id if point_rec and point_rec.state_id else self.generator_id.state_id
        c_country = point_rec.country_id if point_rec and point_rec.country_id else self.generator_id.country_id

        categories = self.line_ids.mapped('waste_category_id')
        RuleSet = self.env['wm.compliance.rule.set']
        suggested_codes = self.env['wm.compliance.code']
        manifest_required = False

        for category in (categories or [False]):
            rules = RuleSet._get_applicable_rules(
                collection_point=point_rec,
                waste_category=category,
                manifest_type=self._get_manifest_type(),
                date=self.manifest_date or fields.Date.today(),
                country=c_country,
                state=c_state
            )
            if rules:
                best_rule = rules[0]
                suggested_codes |= best_rule.required_code_ids
                if best_rule.requires_manifest:
                    manifest_required = True

        if suggested_codes:
            self.compliance_code_ids = [(6, 0, (self.compliance_code_ids | suggested_codes).ids)]

        if not manifest_required and categories:
            return {'warning': {
                'title': _("Manifest May Not Be Required"),
                'message': _("No active compliance rule for this region/category requires a manifest. Verify before submitting."),
            }}

    def _set_workflow_state(self, new_state):
        """Move the manifest along its workflow. Reached only from the action
        buttons, which validate the source state; direct writes of ``state``
        by normal users are refused in ``write``."""
        self.ensure_one()
        self.sudo().write({'state': new_state})

    def action_submit(self):
        """
        Submit the manifest to the regulatory authority by transitioning it to
        'submitted' state, generating a SHA-256 submission certificate, and
        emailing the compliance officer.
        """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Manifest can only be submitted from Draft state."))
            if not rec.line_ids:
                raise UserError(_(
                    "Manifest '%s' has no waste lines: add at least one line before submitting.") % rec.name)

            # Enforce required compliance codes at submission time
            RuleSet = self.env['wm.compliance.rule.set']
            point = getattr(rec.generator_id, 'collection_point_ids', False)
            point_rec = point[0] if point else False
            c_state = point_rec.state_id if point_rec and point_rec.state_id else rec.generator_id.state_id
            c_country = point_rec.country_id if point_rec and point_rec.country_id else rec.generator_id.country_id
            categories = rec.line_ids.mapped('waste_category_id')

            required_codes = self.env['wm.compliance.code']
            for cat in (categories or [False]):
                rules = RuleSet._get_applicable_rules(
                    collection_point=point_rec,
                    waste_category=cat,
                    manifest_type=rec._get_manifest_type(),
                    date=rec.manifest_date or fields.Date.today(),
                    country=c_country,
                    state=c_state
                )
                if rules:
                    required_codes |= rules[0].required_code_ids

            # Every required code must be attached, not just one of them
            missing_codes = required_codes - rec.compliance_code_ids
            if missing_codes:
                missing = missing_codes.mapped('name')
                code_str = ', '.join(filter(None, missing)) if any(missing) else _("Required compliance codes")
                raise UserError(_(
                    "This waste stream/region combination requires mandatory compliance codes (%s) to be attached before submission."
                ) % code_str)

            rec._set_workflow_state('submitted')
            # Auto-log custody milestone
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'generated',
                'location': rec.generator_id.city or rec.generator_id.name,
                'company_id': rec.company_id.id,
                'notes': _("Manifest generated and submitted by %s") % self.env.user.name,
            })
            rec.action_export_and_notify()

    def action_collect(self):
        """
        Transition the manifest from 'submitted' to 'collected' state and log
        the collection milestone in the chain of custody.
        """
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_("Manifest must be in Submitted state to be marked as Collected."))
            rec._set_workflow_state('collected')
            # Auto-log custody milestone
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'collected',
                'location': rec.generator_id.city or rec.generator_id.name,
                'company_id': rec.company_id.id,
                'notes': _("Consignment collected by %s") % (rec.transporter_id.name or 'Transporter'),
            })

    def action_dispose(self):
        """
        Mark the manifest as fully disposed by updating state to 'disposed',
        recording the disposal facility, closing chain-of-custody, and
        automatically issuing the Certificate of Destruction.
        """
        for rec in self:
            if rec.state != 'collected':
                raise UserError(_("Manifest must be in Collected state to be marked as Disposed."))
            # A Certificate of Destruction certifies the disposed quantity,
            # so an empty manifest (no lines / zero total) cannot be disposed.
            if float_compare(rec.total_quantity or 0.0, 0.0, precision_digits=6) <= 0:
                raise UserError(_(
                    "Manifest %(name)s has no waste quantity recorded. A "
                    "Certificate of Destruction cannot be issued for an empty "
                    "manifest: add the disposed waste lines with their "
                    "quantities before marking it as Disposed.",
                    name=rec.name or rec.display_name,
                ))
            # Auto-log the custody milestone before the manifest is locked as
            # disposed: custody rows cannot be added afterwards.
            self.env['wm.compliance.custody'].create({
                'manifest_id': rec.id,
                'action': 'disposed',
                'location': rec.disposal_facility_id.name,
                'company_id': rec.company_id.id,
                'notes': _("Consignment treated/disposed at %s") % (rec.disposal_facility_id.name or 'Facility'),
            })
            rec._set_workflow_state('disposed')
            # Auto-generate & issue Certificate of Destruction
            rec._auto_issue_compliance_certificate()

    def _auto_issue_compliance_certificate(self):
        """Auto-generate and issue Certificate of Destruction upon manifest disposal."""
        Cert = self.env['wm.compliance.certificate'].sudo()
        kg_uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        for manifest in self:
            existing_cert = Cert.search([('manifest_id', '=', manifest.id)], limit=1)
            if not existing_cert and manifest.disposal_facility_id:
                seq_no = self.env['ir.sequence'].next_by_code('wm.compliance.certificate') or _("COD/%s") % manifest.name
                cert = Cert.create({
                    'name': _("Certificate of Disposal - %s") % manifest.name,
                    'manifest_id': manifest.id,
                    'certificate_type': 'destruction',
                    'facility_id': manifest.disposal_facility_id.id,
                    # Certify the real disposed quantity (never a placeholder)
                    'quantity': manifest.total_quantity,
                    # total_quantity is normalised to kg
                    'uom_id': kg_uom.id if kg_uom else False,
                    'certificate_no': seq_no,
                    'state': 'draft',
                    'company_id': manifest.company_id.id,
                })
                try:
                    # Roll back only the failed issue (e.g. PDF rendering), keeping
                    # the disposal and the draft certificate
                    with self.env.cr.savepoint():
                        cert.action_issue()
                except Exception as e:
                    _logger.warning("Failed to auto-issue compliance certificate for manifest %s: %s", manifest.name, e)
                    manifest.message_post(
                        body=_("Warning: Automatic compliance certificate issuance failed: %s. Certificate %s remains in draft.") % (
                            str(e), cert.name or cert.certificate_no or ''
                        )
                    )

    def action_export_and_notify(self):
        """
        Generate a PDF export of the manifest, attach it to the chatter, and
        send a notification email to all configured compliance recipients for
        record keeping.
        """
        self.ensure_one()
        # Idempotent: the PDF is signed once, and stakeholders are emailed once.
        # Re-clicking only re-attaches the existing signed copy to the chatter.
        if not self.signature_id:
            self._generate_signed_pdf()
        if self.notified_at:
            self.message_post(
                body=_("Manifest was already exported and notified on %s.") % self.notified_at,
                attachment_ids=[self.signature_id.pdf_attachment_id.id] if self.signature_id and self.signature_id.pdf_attachment_id else [])
            return

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

        self.sudo().with_context(bypass_compliance_lock=True).write({'notified_at': fields.Datetime.now()})

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
        self.sudo().with_context(bypass_compliance_lock=True).write({'signature_id': sig.id})


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
    collection_order_id = fields.Many2one(
        'wm.collection.order', string='Collection Order', copy=False, index='btree_not_null',
        ondelete='set null', readonly=True,
        help="The collection order this waste line was taken from.")

    @api.model
    def _convert_quantity_to_kg(self, quantity, uom):
        """Convert ``quantity`` expressed in ``uom`` to the kg reference unit.

        Quantities without a UoM, or whose UoM does not share a reference
        with kg (e.g. litres, units), are returned unchanged.
        """
        if not quantity or not uom:
            return quantity or 0.0
        kg = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not kg or uom == kg:
            return quantity
        uom = uom.sudo()
        if not uom._has_common_reference(kg.sudo()):
            return quantity
        return uom._compute_quantity(quantity, kg, round=False)

    def _get_quantity_kg(self):
        """Return this line's quantity converted to kg when possible."""
        self.ensure_one()
        return self._convert_quantity_to_kg(self.quantity, self.uom_id)

    def _get_total_quantity_kg(self):
        """Sum the quantities of these lines, normalised to kg."""
        return sum(line._get_quantity_kg() for line in self)

    def _check_manifest_editable(self, manifests):
        """Lines may only change while their manifest is still a draft."""
        if self.env.su:
            return
        if manifests.filtered(lambda m: m.state != 'draft'):
            raise UserError(_(
                "Lines of a submitted manifest cannot be added, modified or deleted."
            ))

    def _trigger_target_recompute(self, extra_manifests=None):
        """
        Invalidate and recompute linked compliance target achievement
        percentages whenever manifest quantities change, keeping regulatory
        performance indicators current.
        """
        manifests = self.mapped('manifest_id')
        if extra_manifests:
            manifests |= extra_manifests
        if manifests:
            manifests._trigger_target_recompute()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        if not self.env.context.get('wm_manifest_creating'):
            manifest_ids = {vals.get('manifest_id') for vals in vals_list if vals.get('manifest_id')}
            self._check_manifest_editable(self.env['wm.compliance.manifest'].browse(manifest_ids))
        records = super().create(vals_list)
        records._trigger_target_recompute()
        return records

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        manifests = self.mapped('manifest_id')
        if vals.get('manifest_id'):
            manifests |= self.env['wm.compliance.manifest'].browse(vals['manifest_id'])
        self._check_manifest_editable(manifests)
        extra_manifests = None
        if 'manifest_id' in vals:
            extra_manifests = self.mapped('manifest_id')
        res = super().write(vals)
        if any(f in vals for f in ['quantity', 'uom_id', 'waste_category_id', 'manifest_id']):
            self._trigger_target_recompute(extra_manifests=extra_manifests)
        return res

    def unlink(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        manifests = self.mapped('manifest_id')
        self._check_manifest_editable(manifests)
        partners = manifests.mapped('generator_id') | manifests.mapped('transporter_id')
        partner_ids = partners.ids
        res = super().unlink()
        if partner_ids:
            targets = self.env['wm.compliance.target'].search([('partner_id', 'in', partner_ids)])
            if targets:
                for t in targets:
                    t._compute_achieved_quantity()
        return res
