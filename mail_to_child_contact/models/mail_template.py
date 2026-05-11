# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bashir Muhammed A (odoo@cybrosys.com
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
from odoo import models


class MailTemplate(models.Model):
    """Inherit the class to send mail to all customer contacts."""
    _inherit = "mail.template"

    def _generate_template_recipients(self, res_ids, render_fields,
                                      allow_suggested=False,
                                      find_or_create_partners=False,
                                      render_results=None):
        """
        Override to add all contacts under the same commercial partner.
        """
        # Call the parent method to get standard recipients
        render_results = super()._generate_template_recipients(
            res_ids, render_fields,
            allow_suggested=allow_suggested,
            find_or_create_partners=find_or_create_partners,
            render_results=render_results
        )
        # Only proceed if we have results with partner_ids
        if not render_results:
            return render_results
        # For each record, add all contacts under the same commercial partner
        for res_id in res_ids:
            if res_id not in render_results:
                continue
            partner_ids_list = render_results[res_id].get('partner_ids', [])
            if not partner_ids_list:
                continue
            # Get the first partner ID from the list
            first_partner_id = partner_ids_list[0]
            # Search for all partners with the same commercial_partner_id
            partner_to_ids = self.env['res.partner'].sudo().search([
                ('commercial_partner_id', '=', first_partner_id)
            ])
            # Add all found partners to the recipient list
            for rec in partner_to_ids:
                if rec.id not in partner_ids_list:
                    render_results[res_id]['partner_ids'].append(rec.id)

        return render_results
