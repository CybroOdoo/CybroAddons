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
import os
import shutil
from ..models import docusign
from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """ Inheriting sale order to add button for sending documents"""
    _inherit = 'sale.order'

    docusign_line_ids = fields.One2many('docusign.lines', 'docusign_id',
                                        readonly=True,
                                        help="Details of sent documents")
    credentials_id = fields.Many2one("docusign.credentials",
                                     string="Docusign Credential",
                                     help="Choose Credential")

    def action_send_document(self):
        """ Function to open the wizard for sending documents """
        view_id = self.env.ref(
            'docusign_odoo_connector.send_document_view_form').id
        return {
            'name': self.env._("Send Documents"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'send.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_email_id': self.partner_id.id,
                'default_res_id': self.id,
            }
        }

    def action_download_document(self):
        """
            This method downloads documents associated with the current object's
             DocuSign credentials and attaches them as binary data to the
             corresponding record.
        """
        if self.credentials_id:
            credentials = self.credentials_id
            for document in self.docusign_line_ids:
                if document.status == 'completed' and document.signed_document:
                    continue
                envelope_id = document.envelope_id
                if envelope_id:
                    docu_status, complete_path = docusign.download_documents(
                        credentials.integrator_key,
                        envelope_id, credentials.private_key_ids,
                        credentials.user_id_data,
                        credentials.account_id_data,
                        environment=getattr(credentials, 'environment', 'demo'))
                    if complete_path != '':
                        path_split = complete_path.rsplit('/', 1)
                        attach_file_name = path_split[1]
                        folder_path = path_split[0]
                        with open(complete_path, "rb") as open_file:
                            file_content = open_file.read()
                        existing_attachment = self.env['ir.attachment'].search([
                            ('res_model', '=', self._name),
                            ('res_id', '=', self.id),
                            ('name', '=', attach_file_name)
                        ], limit=1)
                        if not existing_attachment:
                            values = {'name': attach_file_name,
                                      'type': 'binary',
                                      'res_id': self.id,
                                      'res_model': self._name,
                                      'raw': file_content,
                                      'index_content': 'image',
                                      'store_fname': attach_file_name,
                                      }
                            attach_id = self.env['ir.attachment'].create(values)
                            raw_data = attach_id.raw
                        else:
                            raw_data = existing_attachment.raw

                        if not document.signed_document:
                            document.signed_document = raw_data
                        if docu_status:
                            document.status = docu_status
                        os.remove(complete_path)
                        if os.path.exists(folder_path):
                            shutil.rmtree(folder_path)
                    elif docu_status:
                        document.status = docu_status
                else:
                    raise UserError(self.env._('No agreement documents are sent'))
        else:
            raise UserError(self.env._('Please select credential'))
