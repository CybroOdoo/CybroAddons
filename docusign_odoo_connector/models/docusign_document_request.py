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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import json
import logging
import os
import shutil
import time
from collections import defaultdict
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from . import docusign

_logger = logging.getLogger(__name__)


class DocusignDocumentRequest(models.Model):
    """Model to manage document signing requests with DocuSign."""
    _name = 'docusign.document.request'
    _description = 'DocuSign Document Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Document Request Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._('New'),
        tracking=True,
        help="Document request number."
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'docusign_request_partner_rel',
        'request_id',
        'partner_id',
        string='Contacts',
        required=True,
        tracking=True,
        help="Select contacts to receive documents for signing."
    )
    expiry_date = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=7),
        tracking=True,
        help="Expiration date for document signing."
    )
    document_ids = fields.Many2many(
        'ir.attachment',
        'docusign_request_attachment_rel',
        'request_id',
        'attachment_id',
        string='Documents',
        required=False,
        help="Upload or select PDF documents to be signed."
    )
    selection_type = fields.Selection(
        [
            ('mandatory', 'Mandatory'),
            ('custom', 'Custom')
        ],
        string='Document Criteria',
        default='mandatory',
        required=True,
        tracking=True,
        help="Mandatory: All documents will be sent to all selected customers.\n"
             "Custom: Select which documents are sent to which customers."
    )
    @api.model
    def _is_multi_company(self):
        """Check whether multi-company environment is active."""
        return bool(
            self.env.user.has_group('base.group_multi_company')
            or len(self.env.companies) > 1
            or len(self.env.user.company_ids) > 1
            or self.env['res.company'].sudo().search_count([]) > 1
        )

    @api.model
    def _default_company_id(self):
        """Do not auto-fill company if multi-company is enabled; auto-fill if single company."""
        if self._is_multi_company():
            return False
        return self.env.company

    @api.model
    def _default_credentials_id(self):
        """Auto-fill credentials only if single company."""
        if self._is_multi_company():
            return False
        return self._get_default_credentials(self.env.company)

    @api.model
    def default_get(self, fields_list):
        """Ensure company and credentials are automatically added in single company mode."""
        res = super().default_get(fields_list)
        if not self._is_multi_company():
            company = self.env.company
            res['company_id'] = company.id
            credential = self._get_default_credentials(company)
            if credential:
                res['credentials_id'] = credential.id
        else:
            if 'company_id' in fields_list:
                res['company_id'] = False
            if 'credentials_id' in fields_list:
                res['credentials_id'] = False
        return res

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self._default_company_id(),
        domain=lambda self: [('id', 'in', self.env.companies.ids)],
        help="Company associated with this document request."
    )
    credentials_id = fields.Many2one(
        'docusign.credentials',
        string='DocuSign Credential',
        default=lambda self: self._default_credentials_id(),
        compute='_compute_credentials_id',
        store=True,
        readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="DocuSign account credentials used for sending documents."
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('sent', 'Document Sent'),
            ('partially_signed', 'Partially Signed'),
            ('fully_signed', 'Fully Signed')
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
        help="Status of document request:\n"
             "- Draft: Initial state.\n"
             "- Document Sent: Documents sent to recipients.\n"
             "- Partially Signed: Some recipients signed.\n"
             "- Fully Signed: All recipients signed."
    )
    custom_line_ids = fields.One2many(
        'docusign.document.request.line',
        'request_id',
        string='Custom Document Assignments',
        copy=True,
        help="Specify which documents are sent to which customers when Custom is selected."
    )
    docusign_line_ids = fields.One2many(
        'docusign.lines',
        'request_id',
        string='DocuSign Lines',
        readonly=True,
        help="Details of envelopes sent via DocuSign."
    )
    reminder_sent = fields.Boolean(
        default=False,
        copy=False,
        help="Flag indicating if the automated reminder email has been sent."
    )

    def _get_default_credentials(self, company=None):
        """Helper to find the appropriate DocuSign credentials for a company."""
        target_company = company or self.company_id
        if not target_company:
            if not self._is_multi_company():
                target_company = self.env.company
            else:
                return self.env['docusign.credentials']
        credential = self.env['docusign.credentials'].sudo().search([
            ('company_id', '=', target_company.id)
        ], limit=1)
        if not credential:
            credential = self.env['docusign.credentials'].sudo().search([
                ('company_id', '=', False)
            ], limit=1)
        if not credential and not self._is_multi_company():
            credential = self.env['docusign.credentials'].sudo().search([], limit=1)
        return credential

    @api.depends('company_id')
    def _compute_credentials_id(self):
        for record in self:
            if record.company_id:
                record.credentials_id = record._get_default_credentials(record.company_id)
            elif not record._is_multi_company():
                record.credentials_id = record._get_default_credentials(self.env.company)
            else:
                record.credentials_id = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            credential = self._get_default_credentials(self.company_id)
            if credential:
                self.credentials_id = credential
            else:
                self.credentials_id = False
                return {
                    'warning': {
                        'title': self.env._("No Active DocuSign Credential"),
                        'message': self.env._(
                            "The selected company '%(company)s' has no active DocuSign credentials. "
                            "Please create and configure credentials for this company in DocuSign Setup.",
                            company=self.company_id.name
                        ),
                    }
                }
        else:
            self.credentials_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('docusign.document.request') or self.env._('New')
        return super().create(vals_list)

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.expiry_date and record.expiry_date < today:
                raise ValidationError(self.env._("Expiry date cannot be set in the past."))

    @api.onchange('selection_type', 'partner_ids', 'document_ids')
    def _onchange_selection_type(self):
        """Auto-populate custom lines when switching to 'custom'."""
        if self.selection_type == 'custom' and not self.custom_line_ids and self.partner_ids:
            lines = []
            for partner in self.partner_ids:
                lines.append((0, 0, {
                    'partner_id': partner.id,
                    'document_ids': [(6, 0, self.document_ids.ids)],
                }))
            self.custom_line_ids = lines

    def action_draft(self):
        """Reset request back to Draft state."""
        self.write({
            'state': 'draft',
            'reminder_sent': False,
        })
        self.message_post(body=self.env._("Document request reset to Draft."))

    def _get_document_assignments(self):
        """
        Returns a dict mapping res.partner record -> ir.attachment recordset
        based on selection_type criteria.
        """
        self.ensure_one()
        assignments = defaultdict(lambda: self.env['ir.attachment'])
        if self.selection_type == 'mandatory':
            if not self.partner_ids:
                raise UserError(self.env._("Please select at least one customer."))
            if not self.document_ids:
                raise UserError(self.env._("Please select at least one document."))
            for partner in self.partner_ids:
                assignments[partner] = self.document_ids
        else:
            if not self.custom_line_ids:
                raise UserError(self.env._("Please configure the custom document assignment lines for customers."))
            for line in self.custom_line_ids:
                if not line.partner_id:
                    raise UserError(self.env._("Customer is required on all custom assignment lines."))
                if not line.document_ids:
                    raise UserError(self.env._(
                        "Please assign at least one document to customer '%(partner)s'.",
                        partner=line.partner_id.name
                    ))
                assignments[line.partner_id] |= line.document_ids

        # Validate that all recipients have an email configured
        for partner in assignments.keys():
            if not partner.email:
                raise UserError(self.env._(
                    "Customer '%(partner)s' does not have an email address configured.",
                    partner=partner.name
                ))

        return assignments

    @api.model
    def action_open_document_wizard(self, attachment_ids=None, request_id=None, partner_ids=None):
        """Open the SendDocument wizard to configure fields on the given attachment(s)."""
        request = self.browse(request_id) if request_id else self
        if partner_ids:
            partner_recs = self.env['res.partner'].browse(partner_ids).exists()
        elif request and request.exists():
            partner_recs = request.partner_ids
        else:
            partner_recs = self.env['res.partner']

        doc_req_id = request.id if (request and request.exists()) else False
        req_name = request.name if (request and request.exists()) else self.env._("New")

        if not attachment_ids:
            if request and request.document_ids:
                attachment_ids = request.document_ids.ids
            else:
                raise UserError(self.env._("No document found to configure fields."))
        elif isinstance(attachment_ids, int):
            attachment_ids = [attachment_ids]

        valid_attachments = self.env['ir.attachment'].browse(attachment_ids).exists()
        if not valid_attachments:
            raise UserError(self.env._("Selected document attachment does not exist."))

        first_att = valid_attachments[0]
        remaining = [att.id for att in valid_attachments[1:]]

        raw = first_att.raw
        if hasattr(raw, 'to_base64'):
            file_data = raw.to_base64()
        elif isinstance(raw, (bytes, bytearray, memoryview)):
            file_data = base64.b64encode(bytes(raw)).decode('ascii')
        elif isinstance(raw, str):
            file_data = raw
        else:
            file_data = False

        view_id = self.env.ref('docusign_odoo_connector.send_document_view_form').id
        partner_names = ", ".join(partner_recs.mapped('name'))
        wizard = self.env['send.document'].create({
            'document_request_id': doc_req_id,
            'attachment_id': first_att.id,
            'reference': first_att.name or req_name,
            'file': file_data,
            'partner_ids': [(6, 0, partner_recs.ids)],
            'partner_names': partner_names,
            'email_id': partner_recs[:1].id if partner_recs else False,
            'data': first_att.docusign_tabs or False,
            'remaining_attachment_ids': json.dumps(remaining),
        })
        return {
            'name': self.env._("Configure Document Fields: %(document)s", document=first_att.name or self.env._("Document")),
            'type': 'ir.actions.act_window',
            'res_model': 'send.document',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'flags': {'mode': 'edit'},
            'context': {
                'default_document_request_id': doc_req_id,
                'default_attachment_id': first_att.id,
            }
        }

    def action_send_document(self):
        """Send documents to customers via DocuSign based on criteria."""
        self.ensure_one()
        credentials = self.credentials_id or self._get_default_credentials(self.company_id)
        if not credentials:
            raise UserError(self.env._(
                "The selected company '%(company)s' has no active DocuSign credentials. "
                "Please create and configure credentials for this company in DocuSign Setup before sending documents.",
                company=self.company_id.name or self.env._("Unknown")
            ))

        if self.selection_type == 'mandatory':
            if not self.document_ids:
                raise UserError(self.env._("Please select at least one document."))
            missing_fields_docs = [doc.name for doc in self.document_ids if not doc.docusign_tabs]
            if missing_fields_docs:
                raise UserError(self.env._(
                    "You need to add fields in the mandatory document(s): %(docs)s.\n"
                    "Please configure the fields for each document before sending.",
                    docs=", ".join(missing_fields_docs)
                ))
        elif self.selection_type == 'custom':
            all_custom_docs = self.custom_line_ids.mapped('document_ids')
            if not all_custom_docs:
                raise UserError(self.env._("Please upload and assign at least one document in the Custom Assignment table."))
            missing_fields_docs = [doc.name for doc in all_custom_docs if not doc.docusign_tabs]
            if missing_fields_docs:
                raise UserError(self.env._(
                    "You need to add fields in the custom document(s): %(docs)s.\n"
                    "Please configure the fields for each document before sending.",
                    docs=", ".join(missing_fields_docs)
                ))

        assignments = self._get_document_assignments()

        for partner, docs in assignments.items():
            for doc in docs:
                file_content = doc.raw
                base_url = self[:1].get_base_url()
                webhook_url = f"{base_url.rstrip('/')}/docusign/webhook" if base_url else None

                tabs_data = None
                if doc.docusign_tabs:
                    try:
                        raw_tabs = json.loads(doc.docusign_tabs)
                        if isinstance(raw_tabs, list):
                            matched = None
                            for tab_dict in raw_tabs:
                                if isinstance(tab_dict, dict) and tab_dict.get('recipient') == partner.name:
                                    matched = tab_dict
                                    break
                            if not matched:
                                partner_idx = list(self.partner_ids.ids).index(partner.id) if partner.id in self.partner_ids.ids else -1
                                if 0 <= partner_idx < len(raw_tabs):
                                    matched = raw_tabs[partner_idx]
                                elif len(raw_tabs) == 1:
                                    matched = raw_tabs[0]
                            if matched:
                                tabs_data = [matched]
                        elif isinstance(raw_tabs, dict):
                            tabs_data = [raw_tabs]
                    except Exception as e:
                        _logger.warning("Could not parse docusign_tabs for document %s: %s", doc.name, e)
                        tabs_data = None

                response = docusign.action_send_docusign_file(
                    credentials.user_id_data,
                    credentials.account_id_data,
                    credentials.integrator_key,
                    credentials.private_key_ids,
                    doc.name or "Document.pdf",
                    file_content,
                    [partner.name],
                    [partner.email],
                    tabs_data,
                    webhook_url=webhook_url,
                    environment=getattr(credentials, 'environment', 'demo')
                )

                envelope_id = getattr(response, 'envelope_id', False)
                status = getattr(response, 'status', 'sent')

                self.env['docusign.lines'].create({
                    'request_id': self.id,
                    'partner_id': partner.id,
                    'document': doc.name or 'Document',
                    'send_to': partner.email,
                    'status': status,
                    'envelope_id': envelope_id,
                })

        self.write({'state': 'sent'})
        self.message_post(body=self.env._("Document(s) successfully sent to recipient(s) via DocuSign."))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("Documents sent successfully! Status changed to 'Document Sent'."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_download_document(self):
        """
        Download documents associated with DocuSign credentials and attach them
        as binary data to the corresponding lines and record (same as sale.order).
        """
        return self.action_update_status()

    def _sync_document_status(self, target_envelope_id=None):
        """
        Safely check envelope statuses from DocuSign, download signed documents,
        and update the request state to 'partially_signed' or 'fully_signed'.
        Can be safely called by webhook or cron in real-time background.
        """
        for record in self:
            lines = record.docusign_line_ids
            if target_envelope_id:
                lines = lines.filtered(lambda line: line.envelope_id == target_envelope_id)
            if not lines:
                continue
            credentials = record.credentials_id or record._get_default_credentials(record.company_id)
            if not credentials:
                continue

            for document in lines:
                if document.status == 'completed' and document.signed_document:
                    continue

                envelope_id = document.envelope_id
                if not envelope_id:
                    continue

                try:
                    with self.env.cr.savepoint():
                        docu_status, complete_path = docusign.download_documents(
                            credentials.integrator_key,
                            envelope_id, credentials.private_key_ids,
                            credentials.user_id_data,
                            credentials.account_id_data,
                            environment=getattr(credentials, 'environment', 'demo')
                        )
                        if complete_path:
                            path_split = complete_path.rsplit('/', 1)
                            attach_file_name = path_split[1]
                            folder_path = path_split[0]
                            with open(complete_path, "rb") as open_file:
                                file_content = open_file.read()
                            existing_attachment = self.env['ir.attachment'].sudo().search([
                                ('res_model', '=', record._name),
                                ('res_id', '=', record.id),
                                ('name', '=', attach_file_name)
                            ], limit=1)
                            if not existing_attachment:
                                values = {
                                    'name': attach_file_name,
                                    'type': 'binary',
                                    'res_id': record.id,
                                    'res_model': record._name,
                                    'raw': file_content,
                                    'index_content': 'image',
                                    'store_fname': attach_file_name,
                                }
                                attach_id = self.env['ir.attachment'].sudo().create(values)
                                raw_data = attach_id.raw
                            else:
                                raw_data = existing_attachment.raw
                            document.sudo().write({
                                'signed_document': raw_data,
                                'status': docu_status or 'completed',
                            })
                            try:
                                if os.path.exists(complete_path):
                                    os.remove(complete_path)
                                if os.path.exists(folder_path):
                                    shutil.rmtree(folder_path)
                            except Exception as e:
                                _logger.debug("Failed to remove temporary file: %s", e)
                        elif docu_status:
                            document.sudo().write({'status': docu_status})
                except Exception as e:
                    _logger.warning("Error syncing DocuSign envelope %s: %s", envelope_id, e)

            try:
                with self.env.cr.savepoint():
                    record._update_signing_state()
            except Exception as e:
                _logger.warning("Error updating signing state for %s: %s", record.id, e)

    def action_update_status(self):
        """
        Check envelope statuses from DocuSign, download signed documents,
        and update the request state to 'partially_signed' or 'fully_signed'.
        """
        for record in self:
            if not record.docusign_line_ids:
                raise UserError(self.env._("No agreement documents are sent"))
            credentials = record.credentials_id or record._get_default_credentials(record.company_id)
            if not credentials:
                raise UserError(self.env._("Please select credential"))
            record._sync_document_status()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("Document signing status updated successfully!"),
                'type': 'info',
                'sticky': False,
            }
        }

    @api.model
    def _cron_auto_update_status(self):
        """
        Scheduled action to automatically check and update signing status
        for all active document requests in the background.
        """
        active_requests = self.sudo().search([
            ('state', 'in', ['sent', 'partially_signed'])
        ])
        for req in active_requests:
            try:
                with self.env.cr.savepoint():
                    req._sync_document_status()
            except Exception as e:
                _logger.warning("Cron auto update failed for DocuSign request %s: %s", req.name, e)

    def _update_signing_state(self):
        """
        Updates state:
        - If all envelopes are 'completed', state becomes 'fully_signed'.
        - If at least one is 'completed' (but not all), state becomes 'partially_signed'.
        - If none are 'completed', state remains 'sent'.
        """
        self.ensure_one()
        if not self.docusign_line_ids:
            return

        total_lines = len(self.docusign_line_ids)
        completed_lines = len(self.docusign_line_ids.filtered(lambda line: line.status == 'completed'))

        if completed_lines == total_lines and total_lines > 0:
            if self.state != 'fully_signed':
                self.write({'state': 'fully_signed'})
                self.message_post(body=self.env._("All documents have been signed! Status changed to Fully Signed."))
        elif completed_lines > 0:
            if self.state != 'partially_signed':
                self.write({'state': 'partially_signed'})
                self.message_post(body=self.env._("Some documents have been signed. Status changed to Partially Signed."))
        else:
            if self.state not in ('draft', 'sent'):
                self.write({'state': 'sent'})

    def action_send_reminder(self):
        """Manually trigger sending reminder emails to pending customers."""
        self.ensure_one()
        if self.state not in ('sent', 'partially_signed'):
            raise UserError(self.env._("Reminders can only be sent for requests in 'Document Sent' or 'Partially Signed' state."))
        sent_partners = self._send_pending_reminders()
        if sent_partners:
            names = ", ".join(sent_partners.mapped('name'))
            self.message_post(body=self.env._("Reminder email sent to: %(names)s", names=names))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': self.env._("Reminder emails sent to: %(names)s", names=names),
                    'type': 'success',
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("No pending customers found for reminder."),
                'type': 'warning',
                'sticky': False,
            }
        }

    def _send_pending_reminders(self):
        """
        Identifies customers who have not yet signed their documents
        and sends them a reminder email.
        """
        self.ensure_one()
        template = self.env.ref('docusign_odoo_connector.email_template_signing_reminder', raise_if_not_found=False)
        if not template:
            return self.env['res.partner']

        # Determine pending customers
        if self.docusign_line_ids:
            pending_lines = self.docusign_line_ids.filtered(lambda line: line.status != 'completed')
            pending_partners = pending_lines.mapped('partner_id')
        else:
            pending_partners = self.partner_ids

        sent_partners = self.env['res.partner']
        for partner in pending_partners:
            if partner.email:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': partner.email,
                        'recipient_ids': [(4, partner.id)],
                    }
                )
                sent_partners |= partner

        if sent_partners:
            self.reminder_sent = True

        return sent_partners

    @api.model
    def _cron_send_signing_reminder(self):
        """
        Cron method to automatically send a reminder mail before the expiry date
        based on the configurable reminder days in Settings.
        """
        icp = self.env['ir.config_parameter'].sudo()
        try:
            reminder_days = icp.get_int('docusign_odoo_connector.reminder_days', default=2)
        except Exception:
            reminder_days = 2
        if not reminder_days or reminder_days <= 0:
            reminder_days = 2

        today = fields.Date.context_today(self)
        target_date = today + timedelta(days=reminder_days)

        records_to_remind = self.search([
            ('state', 'in', ['sent', 'partially_signed']),
            ('expiry_date', '<=', target_date),
            ('expiry_date', '>=', today),
            ('reminder_sent', '=', False),
        ])

        for record in records_to_remind:
            sent_partners = record._send_pending_reminders()
            if sent_partners:
                record.message_post(
                    body=self.env._(
                        "Automated reminder sent (%(days)s days before expiry) to: %(names)s",
                        days=reminder_days,
                        names=", ".join(sent_partners.mapped('name'))
                    )
                )


class DocusignDocumentRequestLine(models.Model):
    """Model to map customer to specific documents in custom mode."""
    _name = 'docusign.document.request.line'
    _description = 'DocuSign Document Request Line'

    request_id = fields.Many2one(
        'docusign.document.request',
        ondelete='cascade',
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        help="Customer who should sign the assigned documents."
    )
    document_ids = fields.Many2many(
        'ir.attachment',
        'docusign_req_line_attachment_rel',
        'line_id',
        'attachment_id',
        string='Documents',
        required=True,
        help="Documents assigned to this customer."
    )
    remarks = fields.Text(
        help="Remarks or notes for this document assignment."
    )
