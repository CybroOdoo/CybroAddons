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
from odoo import fields, models


class ResPartner(models.Model):
    """Inherit res.partner to display signed DocuSign documents."""
    _inherit = 'res.partner'

    docusign_line_ids = fields.One2many(
        'docusign.lines',
        'partner_id',
        string='DocuSign Documents',
        help="All DocuSign documents associated with this partner."
    )
    signed_docusign_line_ids = fields.One2many(
        'docusign.lines',
        'partner_id',
        string='Signed Documents',
        domain=['|', ('status', '=', 'completed'), ('signed_document', '!=', False)],
        help="Signed DocuSign documents associated with this partner."
    )
    signed_document_count = fields.Integer(
        string='Signed Documents Count',
        compute='_compute_signed_document_count',
        help="Count of signed DocuSign documents for this contact."
    )

    def _compute_signed_document_count(self):
        for partner in self:
            partner.signed_document_count = self.env['docusign.lines'].search_count([
                ('partner_id', '=', partner.id),
                '|',
                ('status', '=', 'completed'),
                ('signed_document', '!=', False),
            ])

    def action_view_signed_documents(self):
        """Action for smart button to view signed documents for this contact."""
        self.ensure_one()
        return {
            'name': self.env._('Signed Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'docusign.lines',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.id),
                '|',
                ('status', '=', 'completed'),
                ('signed_document', '!=', False),
            ],
            'context': {'default_partner_id': self.id},
        }
