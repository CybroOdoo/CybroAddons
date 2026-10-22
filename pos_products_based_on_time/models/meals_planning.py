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


class MealsPlanning(models.Model):
    """Time-based product plan: the products shown in the POS for a time
    range, in the selected Point of Sale shops"""
    _name = 'meals.planning'
    _description = "Product Planning"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pos.load.mixin']

    name = fields.Char(required=True, copy=False,
                       help='Name for Product Planning')
    pos_config_ids = fields.Many2many(
        'pos.config', string='Point of Sale', copy=False, required=True,
        help='Choose the Point of Sale shops where this plan is applied')
    time_from = fields.Float(string='From', required=True,
                             help='Start time (24-hour format)')
    time_to = fields.Float(string='To', required=True,
                           help='End time (24-hour format)')
    menu_product_ids = fields.Many2many(
        'product.product', string='Products',
        domain=[('available_in_pos', '=', True)])
    state = fields.Selection([('activated', 'Activated'),
                              ('deactivated', 'Deactivated')],
                             default='deactivated')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.constrains('time_from', 'time_to')
    def _check_time_range(self):
        """Validate the time range. A range that crosses midnight, for
        example 22:00 to 02:00, is allowed"""
        for plan in self:
            if not (0.0 <= plan.time_from <= 24.0
                    and 0.0 <= plan.time_to <= 24.0):
                raise ValidationError(self.env._(
                    "Time values must be between 00:00 and 24:00."))
            if plan.time_from == plan.time_to:
                raise ValidationError(self.env._(
                    "The 'From' time and the 'To' time must be different."))

    def action_activate_meals_plan(self):
        """Change state to activate"""
        self.write({
            'state': 'activated'})

    def action_deactivate_meals_plan(self):
        """Change state to deactivate"""
        self.write({
            'state': 'deactivated'})

    @api.model
    def _load_pos_data_domain(self, data):
        """Load only the plans of the Point of Sale that is being opened"""
        session = data.get('pos.session')
        if session and session.config_id:
            return [('pos_config_ids', 'in', session.config_id.ids)]
        return []

    @api.model
    def _load_pos_data_fields(self, config):
        """To load fields in pos session"""
        return ['name', 'menu_product_ids', 'time_from', 'time_to', 'state']
