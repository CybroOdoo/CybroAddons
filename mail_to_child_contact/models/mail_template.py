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
        # Only proceed if we have results with partner_ids and model is sale or invoice
        if not render_results or self.model not in ('sale.order', 'account.move'):
            return render_results

        # For each record, add all contacts under the same commercial partner
        for res_id in res_ids:
            if res_id not in render_results:
                continue
            partner_ids_list = render_results[res_id].get('partner_ids', [])
            if not partner_ids_list:
                continue
            partners = self.env['res.partner'].browse(partner_ids_list).exists()
            commercial_partners = partners.commercial_partner_id
            if commercial_partners:
                # Search for all partners with the same commercial_partner_id
                child_partners = self.env['res.partner'].search([
                    ('commercial_partner_id', 'in', commercial_partners.ids)
                ])
                existing_ids = set(partner_ids_list)
                # Add all found partners to the recipient list
                for rec in child_partners:
                    if rec.id not in existing_ids:
                        render_results[res_id]['partner_ids'].append(rec.id)
                        existing_ids.add(rec.id)

        return render_results
