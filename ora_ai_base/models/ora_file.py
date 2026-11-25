# -*- coding: utf-8 -*-
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
import base64
import logging
import mimetypes
import os
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class OraFile(models.Model):
    """Used to store custom files."""
    _name = "ora.file"
    _description = "Ora File"

    name = fields.Char(required=True,
                       help="A descriptive name for the file.")
    file = fields.Binary(required=True,
                         help="The actual binary file to be stored.")
    filename = fields.Char(string="File Name",
                           help="Original uploaded file name with extension.")
    id_file = fields.Char(string="File id", readonly=True,
                          help="The unique identifier of the file.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('uploaded', 'Uploaded'),
        ('error', 'Error')
    ], string="Status", default='draft', readonly=True,
       help="Current synchronization state of the file with the AI provider (Draft, Uploaded, or Error).")
    error_message = fields.Text(
        string="Error Details",
        readonly=True,
        help="Technical error details if file upload or synchronization failed."
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        help="Company associated with this knowledge base document."
    )

    @api.constrains('file')
    def _check_file_size(self):
        for rec in self:
            if rec.file:
                raw_data = self._extract_raw_bytes(rec.file)
                if len(raw_data) > MAX_FILE_SIZE:
                    raise ValidationError(self.env._("File size exceeds maximum allowed size (25MB)."))

    @staticmethod
    def _extract_raw_bytes(file_val):
        """Safely extracts raw binary bytes from Odoo 20 binary field / attachment."""
        if not file_val:
            return b''
        if isinstance(file_val, str):
            try:
                return base64.b64decode(file_val)
            except Exception:
                return file_val.encode('utf-8')
        try:
            val = bytes(file_val)
            if val.startswith(b'JVBERi'):
                return base64.b64decode(val)
            return val
        except Exception:
            return bytes(file_val)

    def _detect_mime_type_and_filename(self, decoded_data):
        """Intelligently detects MIME type and ensures a valid extension for Vapi."""
        self.ensure_one()
        rec_file_filename = getattr(self.file, 'filename', None)
        rec_file_mimetype = getattr(self.file, 'mimetype', None)

        raw_name = self.filename or rec_file_filename or self.name or 'document'
        mime_type = rec_file_mimetype or mimetypes.guess_type(raw_name)[0]

        # Magic bytes sniffing if extension guessing failed or octet-stream/empty
        if not mime_type or mime_type in ('application/octet-stream', 'application/x-empty'):
            if decoded_data.startswith(b'%PDF'):
                mime_type = 'application/pdf'
                if not raw_name.lower().endswith('.pdf'):
                    raw_name = f"{raw_name}.pdf"
            elif decoded_data.startswith(b'PK\x03\x04'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                if not raw_name.lower().endswith(('.docx', '.doc')):
                    raw_name = f"{raw_name}.docx"
            elif decoded_data.startswith(b'\xd0\xcf\x11\xe0'):
                mime_type = 'application/msword'
                if not raw_name.lower().endswith('.doc'):
                    raw_name = f"{raw_name}.doc"
            else:
                try:
                    decoded_data[:1024].decode('utf-8')
                    if raw_name.lower().endswith('.csv'):
                        mime_type = 'text/csv'
                    elif raw_name.lower().endswith('.json'):
                        mime_type = 'application/json'
                    elif raw_name.lower().endswith('.md'):
                        mime_type = 'text/markdown'
                    else:
                        mime_type = 'text/plain'
                        if not os.path.splitext(raw_name)[1]:
                            raw_name = f"{raw_name}.txt"
                except UnicodeDecodeError:
                    mime_type = 'application/pdf'
                    if not raw_name.lower().endswith('.pdf'):
                        raw_name = f"{raw_name}.pdf"

        # Ensure filename has an extension corresponding to mime type
        ext = mimetypes.guess_extension(mime_type)
        if ext and not os.path.splitext(raw_name)[1]:
            raw_name = f"{raw_name}{ext}"

        return raw_name, mime_type

    def action_upload_to_vapi(self):
        """Uploads or re-uploads the file to Vapi."""
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_private_api_key')
        if not bearer:
            raise UserError(self.env._("Vapi Private API Key is not configured. Please set it in Settings."))

        for rec in self:
            if not rec.file:
                continue
            raw_data = self._extract_raw_bytes(rec.file)
            if not raw_data:
                rec.write({'state': 'error', 'error_message': self.env._("File is empty.")})
                continue
            if len(raw_data) > MAX_FILE_SIZE:
                rec.write({'state': 'error', 'error_message': self.env._("File size exceeds maximum allowed size (25MB).")})
                continue

            upload_name, mime_type = rec._detect_mime_type_and_filename(raw_data)

            # Delete old file from Vapi if existed
            if rec.id_file:
                try:
                    requests.delete(f"https://api.vapi.ai/file/{rec.id_file}",
                                    headers={"Authorization": f"Bearer {bearer}"},
                                    timeout=10)
                except Exception as err:
                    _logger.debug("Failed to delete superseded remote Vapi file: %s", err)

            url = "https://api.vapi.ai/file"
            files = {
                "file": (upload_name, raw_data, mime_type)
            }
            headers = {
                "Authorization": f"Bearer {bearer}"
            }
            try:
                response = requests.post(url, files=files, headers=headers, timeout=60)
                json_response = response.json()
                if response.ok and json_response.get('id'):
                    vals_to_write = {
                        'id_file': json_response.get('id'),
                        'state': 'uploaded',
                        'error_message': False,
                    }
                    if not rec.filename:
                        vals_to_write['filename'] = upload_name
                    rec.write(vals_to_write)

                    # Update all assistants linked to this file
                    assistants = self.env['ora.ai'].search([('file_ids', 'in', rec.id)])
                    for assistant in assistants:
                        if assistant.id_assistant:
                            assistant.write({})
                else:
                    err = json_response.get('message') or response.text
                    rec.write({'state': 'error', 'error_message': f"Vapi Error: {err}"})
            except Exception as e:
                _logger.exception("Failed to upload file to Vapi: %s", e)
                rec.write({'state': 'error', 'error_message': str(e)})

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new OraFile record and upload the file to VAPI."""
        records = super().create(vals_list)
        records.action_upload_to_vapi()
        return records

    def write(self, vals):
        """Update the OraFile record and propagate changes to VAPI."""
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_private_api_key')
        res = super().write(vals)
        if 'file' in vals or 'filename' in vals:
            self.action_upload_to_vapi()
        elif 'name' in vals and bearer:
            for rec in self:
                if rec.id_file:
                    url = f"https://api.vapi.ai/file/{rec.id_file}"
                    payload = {"name": rec.name}
                    headers = {
                        "Authorization": f"Bearer {bearer}",
                        "Content-Type": "application/json"
                    }
                    try:
                        requests.patch(url, json=payload, headers=headers, timeout=10)
                    except Exception as e:
                        _logger.warning("Failed to rename file %s on Vapi: %s", rec.id_file, e)
        return res

    def unlink(self):
        """Delete OraFile record and remove the associated file from VAPI."""
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_private_api_key')
        for rec in self:
            if rec.id_file and bearer:
                url = f"https://api.vapi.ai/file/{rec.id_file}"
                headers = {"Authorization": f"Bearer {bearer}"}
                try:
                    requests.delete(url, headers=headers, timeout=10)
                except Exception as e:
                    _logger.warning("Failed to delete file %s from Vapi: %s", rec.id_file, e)
        return super().unlink()
