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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MembershipCardLine(models.Model):
    """Stores individual membership product lines for a partner.
    Replaces the removed membership.line model from the old membership
    module which no longer exists in Odoo 19."""

    _name = 'membership.card.line'
    _description = 'Membership Card Line'
    _order = 'date_from desc'

    partner_id = fields.Many2one(
        'res.partner',
        ondelete='cascade',
        required=True,
        help="The partner who holds this membership line.",
    )
    membership_id = fields.Many2one(
        'product.template',
        string='Membership Product',
        required=True,
        domain=[('type', '=', 'service')],
        help="The product/service representing the membership.",
    )
    date_from = fields.Date(
        string='Start Date',
        required=True,
        help="Date from which the membership is valid.",
    )
    date_to = fields.Date(
        string='End Date',
        required=True,
        help="Date until which the membership is valid.",
    )

    @api.constrains('membership_id')
    def _check_membership_id(self):
        for line in self:
            if line.membership_id and line.membership_id.type != 'service':
                raise ValidationError(
                    line.env._(
                        "The membership product '%(product)s' must be a "
                        "service product.",
                        product=line.membership_id.display_name,
                    ),
                )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for line in self:
            if (
                line.date_from
                and line.date_to
                and line.date_to < line.date_from
            ):
                raise ValidationError(
                    line.env._(
                        "End Date (%(end_date)s) cannot be earlier than "
                        "Start Date (%(start_date)s).",
                        end_date=line.date_to,
                        start_date=line.date_from,
                    ),
                )
