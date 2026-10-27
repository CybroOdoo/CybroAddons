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
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_date


class ResPartner(models.Model):
    """Inherit res.partner to add membership card fields and card printing
    action. In Odoo 19 the old membership module was removed, so these
    fields are now defined directly in this module."""

    _inherit = 'res.partner'

    # --- Membership fields (previously from the removed membership module) ---
    free_member = fields.Boolean(
        default=False,
        help="Check if this partner is a free/honorary member "
             "who does not need to purchase a membership product.",
    )
    member_lines = fields.One2many(
        'membership.card.line',
        'partner_id',
        string='Membership Lines',
        help="Membership product lines associated with this partner.",
    )

    def server_action_get_card(self):
        """Fetch data from res.partner to pass into the membership card
        report template and trigger the PDF report action."""
        if not self:
            return False
        self.ensure_one()
        if not self.image_1920:
            raise ValidationError(
                self.env._(
                    "Please provide an image for '%(partner)s' before "
                    "generating the membership card.",
                    partner=self.display_name,
                ),
            )
        if not self.phone:
            raise ValidationError(
                self.env._(
                    "Please provide a phone number for '%(partner)s' before "
                    "generating the membership card.",
                    partner=self.display_name,
                ),
            )
        start_date = ''
        end_date = ''
        membership_products = []

        if not self.free_member:
            # Check if the partner has any membership plan configured
            lines_with_plan = self.member_lines.filtered(
                lambda line: line.membership_id,
            )
            if not lines_with_plan:
                raise ValidationError(
                    self.env._(
                        "Partner '%(partner)s' does not have a membership "
                        "plan. Please add a membership product to print "
                        "the card.",
                        partner=self.display_name,
                    ),
                )

            service_lines = lines_with_plan.filtered(
                lambda line: line.membership_id.type == 'service',
            )
            if not service_lines:
                raise ValidationError(
                    self.env._(
                        "Partner '%(partner)s' does not have a valid "
                        "service membership product. Please configure a "
                        "service product to print the card.",
                        partner=self.display_name,
                    ),
                )

            # Use active line if within period today, otherwise most recent
            today = fields.Date.context_today(self)
            active_lines = service_lines.filtered(
                lambda line: (
                    (not line.date_from or line.date_from <= today)
                    and (not line.date_to or today <= line.date_to)
                ),
            )
            target_line = (
                active_lines[0] if active_lines else service_lines[0]
            )
            start_date = (
                format_date(self.env, target_line.date_from)
                if target_line.date_from
                else ''
            )
            end_date = (
                format_date(self.env, target_line.date_to)
                if target_line.date_to
                else ''
            )
            membership_products = [target_line.membership_id.name]

        company = self.company_id or self.env.company
        image_data = (
            self.image_1920.decode('utf-8')
            if isinstance(self.image_1920, bytes)
            else (self.image_1920 or '')
        )

        data = {
            'name': self.name or '',
            'image': image_data,
            'phone': self.phone or '',
            'function': self.function or '',
            'free_member': self.free_member,
            'membership_product': membership_products,
            'start_date': start_date,
            'end_date': end_date,
            'company_name': company.name or '',
            'company_address': company.street or '',
            'city': company.city or '',
            'country': company.country_id.name or '',
            'state': company.state_id.name or '',
            'company_email': company.email or '',
            'company_phone': company.phone or '',
            'website': company.website or '',
        }
        return (
            self.env.ref('membership_card_odoo.action_membership_card')
            .report_action(None, data=data, config=False)
        )
