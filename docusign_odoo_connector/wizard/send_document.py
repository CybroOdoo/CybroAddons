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
import json
from ..models import docusign
from ..models.edit_document import JSON
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SendDocument(models.TransientModel):
    """ To set up a wizard for uploading pdf and send document."""
    _name = 'send.document'
    _description = "Pdf upload and send Setup wizard"

    email_id = fields.Many2one('res.partner', string='Customer',
                               help="Email Id of customer")
    file = fields.Binary('Preview Document',
                         help="To Preview Document")
    file_name = fields.Char('File Name')
    account_id = fields.Many2one('docusign.credentials', 'DocuSign Account',
                                 help="Docusign Account Id")
    data = JSON('Data', help="Field to store json data")
    check = fields.Boolean('checkbox', help="To check attachment added or not")
    res_id = fields.Many2one("sale.order", string="Source")

    @api.onchange('file')
    def _onchange_check(self):
        """ Function to check whether attachments are uploaded or not """
        if self.file:
            self.check = True
        else:
            self.check = False

    def action_edit_documents(self):
        """ Function to edit documents by inserting fields """
        if self.file:
            raise UserError('Preview')
        else:
            raise UserError('No attachments are added')

    def get_json_data(self, tabs1, res_id):
        """ Function to retrieve the json data """
        wiz = self.browse(res_id)
        wiz.data = json.dumps(tabs1)

    def action_send_documents(self):
        """ Function to send Documents """
        if self.data:
            if self.email_id.email:
                receiver_email = [self.email_id.email]
                receiver_name = [self.email_id.name]
            else:
                raise UserError(
                    'Please add recipients email address')
            account_id = self.env['docusign.credentials'].sudo().search([],
                                                                        limit=1)
            self.account_id = account_id
            if not account_id:
                raise UserError('You need to setup docusign credentials !!!!')

            response = docusign.action_send_docusign_file(account_id.user_id_data,
                                                          account_id.account_id_data,
                                                          account_id.integrator_key,
                                                          account_id.private_key_ids,
                                                          self.file_name,
                                                          self.file,
                                                          receiver_name,
                                                          receiver_email,
                                                          self.data)

            sale_order = self.env['sale.order'].browse(self.res_id.id)
            sale_order.docusign_line_ids = [(0, 0, {
                'document': self.file_name,
                'send_to': receiver_email[0],
                'status': response.status,
                'envelope_id': response.envelope_id
            })]

        else:
            raise UserError('You need to add fields in the document !!!!'
                            '   In the document displayed, by double clicking you can insert fields anywhere in the document')
