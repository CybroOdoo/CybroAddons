# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models


class DocusignLines(models.Model):
    """
    Model for storing DocuSign lines for retrieving send data information.
    This model stores information related to DocuSign lines, including the reference
    to the associated sale order, the recipient to whom the document is sent, and
    the status of the document. """

    _name = 'docusign.lines'
    _description = 'Docusign lines for retrieving send data information'

    docusign_id = fields.Many2one('sale.order',
                                  string='Docusign Reference', index=True,
                                  help="Reference to the associated sale order.")
    document = fields.Char(string="Reference", help="attached document name")
    send_to = fields.Char(string="Send To", help="Mail of receiver")
    status = fields.Char(string="Status", help="Status of sent document")
    envelope_id = fields.Char(string="Envelope ID", help="Envelope ID")
    signed_document = fields.Binary(string="Signed Document", readonly=True,
                                    help="Signed document to download")
