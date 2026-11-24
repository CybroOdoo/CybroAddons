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
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class FreeResource(models.TransientModel):
    """Wizard to specify a period to retrieve available resources."""
    _name = 'free.resource'
    _description = 'Free Resource'

    date_from = fields.Date(
        string="Start Date",
        help="Start date of period for receiving the Free Resource",
    )
    date_to = fields.Date(
        string="End Date",
        help="End date of period for receiving the Free Resource",
    )

    @api.constrains('date_from', 'date_to')
    def _check_date_to_after_date_from(self):
        """Ensure the end date is later than the start date."""
        for record in self:
            if (
                record.date_from
                and record.date_to
                and record.date_to <= record.date_from
            ):
                raise ValidationError(_(
                    "The end date must be after the start date."
                ))

    def get_free_resource(self):
        """Get the list of available resources for the given period."""
        shared_projects = self.env['project.project'].search([
            ('privacy_visibility', 'in', ['portal', 'invited_users']),
        ])
        portal_partner_ids = (
            shared_projects.message_follower_ids.partner_id.filtered(
                lambda p: p.partner_share
            ).ids
        )

        if portal_partner_ids:
            base_domain = [
                ('active', '=', True),
                '|',
                ('share', '=', False),
                ('partner_id', 'in', portal_partner_ids),
            ]
        else:
            base_domain = [
                ('active', '=', True),
                ('share', '=', False),
            ]

        if self.date_from and self.date_to:
            busy_resource_ids = (
                self.env['project.task'].get_free_resource_ids(
                    self.date_from, self.date_to, exclude_task_id=None
                )
            )
            if busy_resource_ids:
                domain = [('id', 'not in', busy_resource_ids)] + base_domain
            else:
                domain = base_domain
        else:
            domain = base_domain

        return {
            'name': (
                _('Free Resources')
                if self.date_from and self.date_to
                else _('All Resources')
            ),
            'view_mode': 'list,form',
            'target': 'current',
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'domain': domain,
        }
