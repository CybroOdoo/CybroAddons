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
import json
from ..models import docusign
from odoo import api, fields, models
from odoo.exceptions import UserError


class SendDocument(models.TransientModel):
    """ To set up a wizard for uploading pdf and send document."""
    _name = 'send.document'
    _description = "Pdf upload and send Setup wizard"

    email_id = fields.Many2one('res.partner', string='Customer',
                               help="Email Id of customer")
    partner_ids = fields.Many2many('res.partner', string='Contacts',
                                   help="Contacts to sign the document")
    partner_names = fields.Char(string='Recipient Names',
                                help="Recipient names for DocuSign tabs")
    file = fields.Binary('Preview Document',
                         help="To Preview Document")
    reference = fields.Char(required=True,
                            help="Reference of the document")
    account_id = fields.Many2one('docusign.credentials', 'DocuSign Account',
                                 help="Docusign Account Id")
    data = fields.Char(help="Field to store json data")
    check = fields.Boolean('checkbox', help="To check attachment added or not")
    res_id = fields.Many2one("sale.order", string="Source", help="Sale order")
    document_request_id = fields.Many2one('docusign.document.request',
                                          help="Document request source")
    attachment_id = fields.Many2one('ir.attachment',
                                    help="Document attachment")
    remaining_attachment_ids = fields.Char(string="Remaining Attachments",
                                           help="JSON array of remaining attachment IDs")

    @api.onchange('file')
    def _onchange_check(self):
        """
        Onchange method triggered when the 'file' field is changed.
        Sets the 'check' field to True if 'file' is not empty,
        otherwise sets it to False.

        This method is intended to automatically update the 'check' field
        based on changes to the 'file' field.
        """
        if self.file:
            self.check = True
        else:
            self.check = False

    def action_edit_documents(self):
        """ Function to edit documents by inserting fields """
        if self.file:
            raise UserError(self.env._('Preview'))
        raise UserError(self.env._('No attachments are added'))

    def get_json_data(self, tabs1, res_id):
        """ Function to retrieve the json data """
        wiz = self.browse(res_id)
        wiz.data = json.dumps(tabs1)

    def action_save_document_fields(self):
        """ Save the configured tabs to the attachment and open next document wizard if any. """
        self.ensure_one()
        if self.attachment_id:
            self.attachment_id.sudo().write({
                'docusign_tabs': self.data or False,
            })

        remaining_ids = []
        if self.remaining_attachment_ids:
            try:
                remaining_ids = json.loads(self.remaining_attachment_ids)
            except Exception:
                remaining_ids = []

        if remaining_ids and self.document_request_id:
            next_attachment_id = remaining_ids.pop(0)
            next_att = self.env['ir.attachment'].browse(next_attachment_id)
            if next_att.exists():
                raw = next_att.raw
                if hasattr(raw, 'to_base64'):
                    next_file = raw.to_base64()
                elif isinstance(raw, (bytes, bytearray, memoryview)):
                    next_file = base64.b64encode(bytes(raw)).decode('ascii')
                elif isinstance(raw, str):
                    next_file = raw
                else:
                    next_file = False
                view_id = self.env.ref('docusign_odoo_connector.send_document_view_form').id
                target_partners = self.partner_ids or (self.document_request_id.partner_ids if self.document_request_id else self.env['res.partner'])
                partner_names = self.partner_names or ", ".join(target_partners.mapped('name'))
                next_wiz = self.env['send.document'].create({
                    'document_request_id': self.document_request_id.id if self.document_request_id else False,
                    'attachment_id': next_att.id,
                    'reference': next_att.name or (self.document_request_id.name if self.document_request_id else self.env._("Document")),
                    'file': next_file,
                    'partner_ids': [(6, 0, target_partners.ids)],
                    'partner_names': partner_names,
                    'email_id': target_partners[:1].id if target_partners else False,
                    'data': next_att.docusign_tabs or False,
                    'remaining_attachment_ids': json.dumps(remaining_ids),
                })
                return {
                    'name': self.env._("Configure Document Fields: %(document)s", document=next_att.name or self.env._("Document")),
                    'type': 'ir.actions.act_window',
                    'res_model': 'send.document',
                    'res_id': next_wiz.id,
                    'view_mode': 'form',
                    'views': [(view_id, 'form')],
                    'view_id': view_id,
                    'target': 'new',
                    'flags': {'mode': 'edit'},
                    'context': {
                        'default_document_request_id': self.document_request_id.id,
                        'default_attachment_id': next_att.id,
                    }
                }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("Document fields saved successfully."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_send_documents(self):
        """ Function to send Documents """
        if self.data:
            if self.email_id.email:
                receiver_email = [self.email_id.email]
                receiver_name = [self.email_id.name]
            else:
                raise UserError(
                    self.env._('Please add recipients email address'))
            account_id = self.res_id.credentials_id
            if not account_id:
                account_id = self.env['docusign.credentials'].sudo().search([], limit=1)
            self.account_id = account_id
            if not account_id:
                raise UserError(self.env._('You need to setup docusign credentials !!!!'))

            tabs_data = json.loads(self.data) if isinstance(self.data, str) else self.data
            base_url = self[:1].get_base_url()
            webhook_url = f"{base_url.rstrip('/')}/docusign/webhook" if base_url else None
            response = docusign.action_send_docusign_file(
                account_id.user_id_data,
                account_id.account_id_data,
                account_id.integrator_key,
                account_id.private_key_ids,
                self.reference,
                self.file,
                receiver_name,
                receiver_email,
                tabs_data,
                webhook_url=webhook_url,
                environment=account_id.environment)

            sale_order = self.env['sale.order'].browse(self.res_id.id)
            sale_order.docusign_line_ids = [(0, 0, {
                'partner_id': self.email_id.id,
                'document': self.reference,
                'send_to': receiver_email[0],
                'status': response.status,
                'envelope_id': response.envelope_id
            })]
        else:
            raise UserError(self.env._(
                'You need to add fields in the document !!!!'
                '   In the document displayed, by double clicking you can insert fields anywhere in the document'
            ))
