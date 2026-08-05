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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    """ Adds the "Submit to Oman E-Invoicing" action/smart button, and recognizes imported PINT OM
    XML files. """
    _inherit = 'account.move'

    l10n_om_edi_document_ids = fields.One2many(
        comodel_name='l10n.om.edi.document', inverse_name='move_id', string="Oman E-Invoicing Documents")
    l10n_om_edi_document_count = fields.Integer(compute='_compute_l10n_om_edi_document_count')
    l10n_om_edi_state = fields.Selection(related='l10n_om_edi_document_ids.l10n_om_edi_state', string="Oman E-Invoicing State")

    @api.depends('l10n_om_edi_document_ids')
    def _compute_l10n_om_edi_document_count(self):
        """ Count this move's Oman E-Invoicing documents, for the smart button's visibility/badge. """
        for move in self:
            move.l10n_om_edi_document_count = len(move.l10n_om_edi_document_ids)

    def _l10n_om_edi_get_or_create_document(self):
        """ Return this move's active (not rejected/cancelled) submission document, creating one
        if none exists yet. """
        self.ensure_one()
        document = self.l10n_om_edi_document_ids.filtered(lambda d: d.l10n_om_edi_state not in ('rejected', 'cancelled'))[:1]
        if not document:
            document = self.env['l10n.om.edi.document'].create({
                'move_id': self.id,
                'company_id': self.company_id.id,
            })
        return document

    def action_l10n_om_edi_submit(self):
        """ Generate the PINT OM + TDD XML and submit them to the company's configured ASP. """
        for move in self:
            document = move._l10n_om_edi_get_or_create_document()
            document._action_submit()

    def action_l10n_om_edi_view_documents(self):
        """ Open the list/form of this move's Oman E-Invoicing documents (the smart button action). """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Oman E-Invoicing Documents",
            'res_model': 'l10n.om.edi.document',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.id)],
        }

    def _get_import_file_type(self, file_data):
        """ Identify PINT OM files (billing and self-billing). """
        # EXTENDS 'account_edi_ubl_cii'
        tree = file_data['xml_tree']
        if tree is not None and tree.findtext('{*}CustomizationID') in (
            'urn:peppol:pint:billing-1@om-1',
            'urn:peppol:pint:selfbilling-1@om-1',
        ):
            return 'account.edi.xml.pint_om'

        return super()._get_import_file_type(file_data)
