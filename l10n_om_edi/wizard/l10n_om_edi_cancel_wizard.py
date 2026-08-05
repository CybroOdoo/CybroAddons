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
from odoo import fields, models, _
from odoo.exceptions import UserError


class L10nOmEdiCancelWizard(models.TransientModel):
    """ Captures a cancellation reason and forwards the cancellation request to the ASP.

    NOTE: Oman's exact cancellation-vs-credit-note rules were not detailed in the regulatory brief
    this module was built against. This wizard is a placeholder; revisit once the Oman Tax
    Authority's rules are confirmed.
    """
    _name = 'l10n.om.edi.cancel.wizard'
    _description = "Oman E-Invoicing Cancellation Wizard"

    document_id = fields.Many2one(comodel_name='l10n.om.edi.document', string="Document", required=True, readonly=True)
    reason = fields.Char(string="Cancellation Reason", required=True)

    def button_confirm_cancel(self):
        """ Validate the reason, ask the ASP connector to cancel, and mark the document cancelled. """
        self.ensure_one()
        if not self.reason.strip():
            raise UserError(_("You must provide a reason for cancelling this document."))

        document = self.document_id
        connector = document.company_id._l10n_om_edi_get_connector()
        if connector.cancel(document.asp_reference, self.reason):
            document.l10n_om_edi_state = 'cancelled'
