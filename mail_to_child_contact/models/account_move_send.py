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
from odoo import api, models


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
            commercial_partners = partners.commercial_partner_id
            child_partners = self.env['res.partner'].with_company(
                move.company_id
            ).search([
                ('commercial_partner_id', 'in', commercial_partners.ids)
            ])
            # Add all found partners to the partners recordset
            partners |= child_partners
        # Apply email filtering if context requires it
        if not self.env.context.get('allow_partners_without_mail'):
            partners = partners.filtered('email')

        return partners
