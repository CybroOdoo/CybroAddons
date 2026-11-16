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

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DocusignLines(models.Model):
    """
    Model for storing DocuSign lines for retrieving send data information.
    This model stores information related to DocuSign lines, including the reference
    to the associated sale order, the recipient to whom the document is sent, and
    the status of the document. """

    _name = 'docusign.lines'
    _description = 'Docusign lines for retrieving send data information'
    _rec_name = 'document'

    docusign_id = fields.Many2one('sale.order',
                                  string='Docusign Reference', index=True,
                                  help="Reference to the associated sale order.")
    request_id = fields.Many2one('docusign.document.request',
                                 string='Document Request', index=True,
                                 help="Reference to the associated document request.")
    partner_id = fields.Many2one('res.partner', string='Contact',
                                 help="Contact associated with this document.")
    document = fields.Char(string="Reference", help="attached document name")
    send_to = fields.Char(help="Mail of receiver")
    status = fields.Char(help="Status of sent document")
    envelope_id = fields.Char(string="Envelope ID", help="Envelope ID")
    signed_document = fields.Binary(readonly=True,
                                    help="Signed document to download")

    def _compute_display_name(self):
        for line in self:
            if line.request_id and line.document:
                line.display_name = f"{line.request_id.name} - {line.document}"
            elif line.request_id:
                line.display_name = line.request_id.name
            elif line.document:
                line.display_name = line.document
            else:
                line.display_name = line.envelope_id or 'Document'

    @api.model
    def _process_docusign_webhook(self, envelope_id, status=None):
        """
        Processes real-time status update from DocuSign webhook.
        """
        lines = self.sudo().search([('envelope_id', '=', envelope_id)])
        if not lines:
            _logger.info("DocuSign Webhook: No docusign.lines found for envelope_id %s", envelope_id)
            return

        # If associated with document requests
        requests = lines.mapped('request_id')
        for req in requests:
            req.sudo()._sync_document_status(target_envelope_id=envelope_id)

        # If associated with sale orders
        sale_orders = lines.mapped('docusign_id')
        for order in sale_orders:
            try:
                order.sudo().action_download_document()
            except Exception as e:
                _logger.warning("Error updating sale order for envelope %s: %s", envelope_id, e)
