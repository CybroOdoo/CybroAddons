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
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    """Extend fleet.vehicle in wm_compliance with compliance certificate relationships."""
    _inherit = 'fleet.vehicle'

    wm_compliance_cert_ids = fields.Many2many(
        'wm.compliance.certificate',
        string='Compliance Certificates',
        help='Active compliance certificates linked to this vehicle'
    )


class ComplianceCertificate(models.Model):
    """Extends Compliance Certificate with digital signature audit and SHA-256 verification."""
    _name = 'wm.compliance.certificate'
    _description = 'Compliance Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'id desc'

    LOCKED_STATES = ['issued']

    name = fields.Char(string='Certificate Name', required=True)
    manifest_id = fields.Many2one('wm.compliance.manifest', string='Linked Manifest', tracking=True)
    certificate_type = fields.Selection([
        ('disposal', 'Disposal'),
        ('recycling', 'Recycling'),
        ('treatment', 'Treatment'),
        ('destruction', 'Destruction')
    ], string='Certificate Type', required=True, default='disposal', tracking=True)

    facility_id = fields.Many2one('wm.disposal.facility', string='Disposal Facility', required=True, tracking=True)
    quantity = fields.Float(string='Quantity', required=True, default=0.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', string='UoM', tracking=True)
    certificate_no = fields.Char(
        string='Certificate No.', required=True, copy=False, tracking=True,
        default=lambda self: _('New'))
    issued_date = fields.Date(
        string='Issued Date',
        required=False,
        tracking=True,
        help='Populated automatically when the certificate is issued. '
             'Leave blank on draft records.',
    )
    signature_id = fields.Many2one('wm.digital.signature', string='Digital Signature', readonly=True, copy=False)
    signature_signer_id = fields.Many2one('res.users', string='Signer', related='signature_id.signer_id', readonly=True)
    signature_signed_at = fields.Datetime(string='Signed At', related='signature_id.signed_at', readonly=True)
    signature_pdf_hash = fields.Char(string='PDF Hash (SHA-256)', related='signature_id.pdf_hash', readonly=True)
    signature_hash_verified = fields.Boolean(string='Signature Verified', related='signature_id.hash_verified', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued')
    ], string='Status', default='draft', required=True, tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Number certificates from the ir.sequence when no number is given."""
        for vals in vals_list:
            if not vals.get('certificate_no') or vals['certificate_no'] == _('New'):
                vals['certificate_no'] = self.env['ir.sequence'].next_by_code(
                    'wm.compliance.certificate') or _('New')
        return super().create(vals_list)

    def copy_data(self, default=None):
        """
        Customize duplicated values per record (safe on multi-record copy):
        suffix the name/number with "(Copy)" and reset the copy to draft.
        """
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for rec, vals in zip(self, vals_list):
            if not default.get('certificate_no'):
                vals['certificate_no'] = _("%s (Copy)", rec.certificate_no or '')
            if not default.get('name'):
                vals['name'] = _("%s (Copy)", rec.name or '')
            if not default.get('state'):
                vals['state'] = 'draft'
        return vals_list

    def action_issue(self):
        """
        Formally issue the compliance certificate by transitioning state to
        'issued', stamping the issue date and generating the signed PDF.
        """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Certificate is already issued."))
            rec.write({
                'state': 'issued',
                # Stamp the issue date at the moment of issuance so draft
                # and issued certificates always carry the correct date.
                'issued_date': fields.Date.context_today(rec),
            })
            rec._generate_signed_pdf()

    def _generate_signed_pdf(self):
        """
        Render the compliance certificate QWeb report to a tamper-evident PDF,
        embedding the SHA-256 hash and issuer signature image for regulatory
        submission.
        """
        self.ensure_one()
        report = self.env.ref('wm_compliance.action_report_compliance_certificate')
        pdf_bytes, report_format = self.env['ir.actions.report']._render_qweb_pdf(report.id, [self.id])
        filename = f"CERTIFICATE_{self.certificate_no.replace('/', '_')}.pdf"
        sig = self.env['wm.digital.signature'].sign_document(self, pdf_bytes, filename)
        self.sudo().with_context(bypass_compliance_lock=True).write({'signature_id': sig.id})

        # Log the attachment in the chatter
        self.message_post(
            body=_("Signed Compliance Certificate generated and attached."),
            attachment_ids=[sig.pdf_attachment_id.id]
        )
