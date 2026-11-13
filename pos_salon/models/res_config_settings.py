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


class ResConfigSettings(models.TransientModel):
    """Expose salon configuration values through POS settings."""

    _inherit = 'res.config.settings'

    pos_is_salon = fields.Boolean(
        string='Is Salon',
        related='pos_config_id.is_salon',
        readonly=False,
        help='Enable salon appointment features for this POS configuration.',
    )
    pos_is_spa = fields.Boolean(
        string='Spa Management',
        related='pos_config_id.is_spa',
        readonly=False,
        help='Enable spa management options for this POS configuration.',
    )
    pos_take_review = fields.Boolean(
        string='Take Review',
        related='pos_config_id.take_review',
        readonly=False,
        help='Enable review collection in the POS workflow.',
    )
    pos_apply_commission = fields.Boolean(
        string='Apply Commission',
        related='pos_config_id.apply_commission',
        readonly=False,
        help='Enable commission handling for the POS configuration.',
    )
    pos_commission_type = fields.Selection(
        string='Commission Mode',
        related='pos_config_id.commission_type',
        readonly=False,
        help='Choose whether commission handling is manual or automatic.',
    )
    pos_commission_percent = fields.Float(
        string='Commission (%)',
        related='pos_config_id.commission_percent',
        readonly=False,
        help='Percentage of the booking amount paid to the specialist.',
    )
    pos_show_appointments = fields.Boolean(
        string='Show Appointments',
        related='pos_config_id.show_appointments',
        readonly=False,
        help='Enable appointment visibility in the POS interface.',
    )
    pos_show_all_appointments = fields.Boolean(
        string='Show All Appointments',
        related='pos_config_id.show_all_appointments',
        readonly=False,
        help='Enable access to all salon appointments in the POS interface.',
    )
    pos_specialist_ids = fields.Many2many(
        string='Specialists',
        related='pos_config_id.specialist_ids',
        readonly=False,
        help='Select the specialists available during appointment booking.',
    )
    pos_amenities_ids = fields.Many2many(
        string='Amenities',
        related='pos_config_id.amenities_ids',
        readonly=False,
        help='Select the amenities available during appointment booking.',
    )
    pos_salon_seats = fields.Integer(
        string='Seats',
        related='pos_config_id.salon_seats',
        readonly=False,
        help='Total number of seats in the salon. 0 means no limit.',
    )

    @api.onchange('pos_show_appointments')
    def _onchange_pos_show_appointments(self):
        """Clear the dependent option when its parent is turned off."""
        if not self.pos_show_appointments:
            self.pos_show_all_appointments = False

    @api.onchange('pos_is_salon')
    def _onchange_pos_is_salon_defaults(self):
        """Turning Salon on enables Show Appointments by default.
        Every other salon option stays off until the owner switches it on."""
        if self.pos_is_salon:
            self.pos_show_appointments = True

    @api.onchange('pos_is_salon', 'pos_module_pos_restaurant')
    def _onchange_pos_salon_restaurant(self):
        if self.pos_is_salon and self.pos_module_pos_restaurant:
            config = self.pos_config_id
            if config.is_salon:
                self.pos_module_pos_restaurant = False
                message = self.env._("This shop is already a Salon. It cannot also be a Bar/Restaurant.")
            else:
                self.pos_is_salon = False
                message = self.env._("This shop is already a Bar/Restaurant. It cannot also be a Salon.")
            return {'warning': {'title': self.env._("Not allowed"), 'message': message}}
