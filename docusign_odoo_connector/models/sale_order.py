# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import os
import shutil
from ..models import docusign
from odoo import fields, models, _
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
            'name': _("Send Documents"),
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
                envelope_id = document.envelope_id
                if envelope_id:
                    docu_status, complete_path = docusign.download_documents \
                        (credentials.integrator_key,
                         envelope_id, credentials.private_key_ids,
                         credentials.user_id_data,
                         credentials.account_id_data)
                    if complete_path != '':
                        path_split = complete_path.rsplit('/', 1)
                        attach_file_name = path_split[1]
                        folder_path = path_split[0]
                        with open(complete_path, "rb") as open_file:
                            encoded_string = base64.b64encode(
                                open_file.read())
                        values = {'name': attach_file_name,
                                  'type': 'binary',
                                  'res_id': self.id,
                                  'res_model': 'crm.lead',
                                  'datas': encoded_string,
                                  'index_content': 'image',
                                  'store_fname': attach_file_name,
                                  }
                        attach_id = self.env['ir.attachment'].create(values)
                        if not document.signed_document:
                            document.signed_document = attach_id.datas
                            document.status = docu_status
                        os.remove(complete_path)
                        if os.path.exists(folder_path):
                            shutil.rmtree(folder_path)
                    self.env.cr.commit()
                else:
                    raise UserError('No agreement documents are sent')
        else:
            raise UserError('Please select credential')


class DocusignLines(models.Model):
    """
    Model for storing DocuSign lines for retrieving send data information.
    This model stores information related to DocuSign lines, including the reference
    to the associated sale order, the recipient to whom the document is sent, and
    the status of the document. """

    _name = 'docusign.lines'
    _description = 'Docusign lines for retrieving send data information'

    docusign_id = fields.Many2one('sale.order', string='Docusign Reference',
                                  index=True,
                                  help="Reference to the associated sale order.")
    document = fields.Char(string="Document", help="attached document name")
    send_to = fields.Char(string="Send To", help="Mail of receiver")
    status = fields.Char(string="Status", help="Status of sent document")
    envelope_id = fields.Char(string="Envelope ID", help="Envelope ID")
    signed_document = fields.Binary(string="Signed Document", readonly=True,
                                    help="Signed document to download")
