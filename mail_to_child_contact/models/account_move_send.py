# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bashir Muhammed A (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api,models


class AccountMoveSend(models.AbstractModel):
    """Inherited the account move send model to add functionality"""
    _inherit = 'account.move.send'

    @api.model
    def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        """
        Override to add all contacts under the same commercial partner.
        """
        # Call parent method to get standard recipients
        partners = super()._get_default_mail_partner_ids(move, mail_template,
                                                         mail_lang)
        # If we have partners, add all contacts under the same commercial partner
        if partners:
            # Get the first partner from the recordset
            first_partner = partners[0]
            # Search for all partners with the same commercial_partner_id
            partner_to_ids = self.env['res.partner'].sudo().search([
                ('commercial_partner_id', '=', first_partner.id)
            ])
            # Add all found partners to the partners recordset
            partners |= partner_to_ids
        # Apply email filtering if context requires it
        if not self.env.context.get('allow_partners_without_mail'):
            partners = partners.filtered('email')

        return partners
