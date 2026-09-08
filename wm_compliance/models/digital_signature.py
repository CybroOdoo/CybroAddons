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
import base64
import hashlib
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DigitalSignature(models.Model):
    """Cryptographic digital signature record storing SHA-256 document checksums."""
    _name = 'wm.digital.signature'
    _description = 'Digital Signature Infrastructure'
    _order = 'id desc'

    res_model = fields.Char(string='Resource Model', required=True, index=True)
    res_id = fields.Integer(string='Resource ID', required=True, index=True)
    signer_id = fields.Many2one('res.users', string='Signer', default=lambda self: self.env.user, required=True)
    signed_at = fields.Datetime(string='Signed At', default=fields.Datetime.now, required=True)
    pdf_attachment_id = fields.Many2one('ir.attachment', string='Signed PDF Attachment', required=True)
    pdf_hash = fields.Char(string='PDF Hash (SHA-256)', size=64, required=True)

    hash_verified = fields.Boolean(
        string='Hash Verified',
        compute='_compute_hash_verified',
        store=False
    )

    def _compute_display_name(self):
        """
        Build a descriptive display name for the digital signature record from
        the signer name and signed date, used in chatter references and audit
        log entries.
        """
        for rec in self:
            if rec.signer_id and rec.signed_at:
                rec.display_name = _("Signature by %s (%s)") % (rec.signer_id.name, rec.signed_at.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                rec.display_name = _("Draft Digital Signature")

    @api.depends('pdf_attachment_id')
    def _compute_hash_verified(self):
        """
        Re-compute the SHA-256 hash of the current document attachment and
        compare it to the stored certificate hash, setting the verified flag to
        indicate document integrity.
        """
        for rec in self:
            if not rec.pdf_attachment_id:
                rec.hash_verified = False
                continue
            try:
                # Odoo 19: use raw to read the direct bytes, fallback to datas base64 decode
                attachment = rec.pdf_attachment_id
                pdf_bytes = attachment.raw or base64.b64decode(attachment.datas or b'')
                if not pdf_bytes:
                    rec.hash_verified = False
                    continue
                current_hash = hashlib.sha256(pdf_bytes).hexdigest()
                rec.hash_verified = (current_hash == rec.pdf_hash)
            except Exception as e:
                _logger.warning("Digital signature hash verification failed for record %s: %s", rec.id, e)
                rec.hash_verified = False

    @api.model
    def sign_document(self, record, pdf_bytes, filename):
        """
        Capture the signer's digital signature, generate the SHA-256 hash of
        the signed document, attach the certified PDF to the record, and mark
        signing as complete.
        """
        if not pdf_bytes:
            raise UserError(_("No document content provided to sign."))

        # Calculate SHA-256 hash
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'raw': pdf_bytes,
            'res_model': record._name,
            'res_id': record.id,
        })

        # Create and return signature record
        return self.create({
            'res_model': record._name,
            'res_id': record.id,
            'signer_id': self.env.user.id,
            'signed_at': fields.Datetime.now(),
            'pdf_attachment_id': attachment.id,
            'pdf_hash': pdf_hash,
        })

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        stored_fields = [f for f in vals if self._fields[f].store]
        if stored_fields:
            raise UserError(_("Digital signatures are legally binding records and cannot be modified."))
        return super(DigitalSignature, self).write(vals)

    def unlink(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        raise UserError(_("Digital signatures are legally binding records and cannot be deleted."))
