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


class PosConfig(models.Model):
    """Extend POS configurations with salon workflow options."""

    _inherit = 'pos.config'

    is_salon = fields.Boolean(
        help='Enable salon appointment features for this POS configuration.',
    )
    is_spa = fields.Boolean(
        string='Spa Management',
        help='Enable spa management options for this POS configuration.',
    )
    take_review = fields.Boolean(
        help='Email the customer a review link when a booking is completed.',
    )
    apply_commission = fields.Boolean(
        help='Enable commission handling for the POS configuration.',
    )
    commission_type = fields.Selection([
        ('manual', 'Manually'),
        ('auto', 'Automatically'),
    ],
        string='Commission Mode',
        default='manual',
        help='Choose whether commission handling is manual or automatic.',
    )
    commission_percent = fields.Float(
        string='Commission (%)',
        default=10.0,
        help='Percentage of the booking amount paid to the specialist as commission.',
    )
    show_appointments = fields.Boolean(
        help='Enable appointment visibility in the POS interface.',
    )
    show_all_appointments = fields.Boolean(
        help='Enable access to all salon appointments in the POS interface.',
    )
    specialist_ids = fields.Many2many(
        'res.partner',
        string='Specialists',
        help='Select the specialists available during appointment booking.',
    )
    amenities_ids = fields.Many2many(
        'product.product',
        help='Select the amenities available during appointment booking.',
    )
    salon_seats = fields.Integer(
        string='Seats',
        default=0,
        help='Total number of seats in the salon. 0 means no limit.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_salon') and 'show_appointments' not in vals:
                vals['show_appointments'] = True
        return super().create(vals_list)

    def write(self, vals):
        newly_salon = self.browse()
        if vals.get('is_salon') and 'show_appointments' not in vals:
            newly_salon = self.filtered(lambda c: not c.is_salon)
        res = super().write(vals)
        if newly_salon:
            newly_salon.write({'show_appointments': True})
        return res

    @api.constrains('is_salon', 'module_pos_restaurant')
    def _check_salon_restaurant(self):
        for config in self:
            if config.is_salon and config.module_pos_restaurant:
                raise ValidationError(self.env._(
                    "'%s' cannot be both a Salon and a Bar/Restaurant. Disable one first.",
                    config.name))

    @api.onchange('is_salon', 'module_pos_restaurant')
    def _onchange_salon_restaurant(self):
        if self.is_salon and self.module_pos_restaurant:
            return {'warning': {
                'title': self.env._("Not allowed"),
                'message': self.env._("Salon and Bar/Restaurant cannot be enabled together."),
            }}