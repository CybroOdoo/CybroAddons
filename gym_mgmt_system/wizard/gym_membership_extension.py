# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta


class GymMembershipExtendWizard(models.TransientModel):
    """Wizard to extend gym membership"""
    _name = 'gym.membership.extend.wizard'
    _description = 'Extend Gym Membership Wizard'

    membership_id = fields.Many2one(
        'gym.membership',
        string='Membership',
        required=True
    )

    member_id = fields.Many2one('res.partner', string='Member', required=True)
    current_end_date = fields.Date(string='Current End Date', related='membership_id.effective_end_date')

    extension_type = fields.Selection([
        ('same_plan', 'Extend with Same Plan Duration'),
        ('custom_days', 'Custom Number of Days'),
        ('new_plan', 'Change to New Membership Plan')
    ], string='Extension Type', required=True, default='same_plan')

    same_plan_duration = fields.Integer(
        string='Plan Duration (Days)',
        compute='_compute_same_plan_duration',
        store=True
    )

    custom_days = fields.Integer(string='Number of Days to Extend', default=30)

    new_membership_plan_id = fields.Many2one('product.product', string='New Membership Plan',
                                             domain="[('membership_date_from', '!=', False)]")
    new_plan_duration = fields.Integer(string='New Plan Duration (Days)')

    extension_days = fields.Integer(string='Total Extension Days', compute='_compute_extension_details', store=True)
    new_end_date = fields.Date(string='New End Date', compute='_compute_extension_details', store=True)
    extension_amount = fields.Float(string='Extension Amount', compute='_compute_extension_details', store=True)

    notes = fields.Text(string='Notes')

    @api.depends('membership_id.membership_duration')
    def _compute_same_plan_duration(self):
        """Compute the same plan duration from membership"""
        for wizard in self:
            wizard.same_plan_duration = wizard.membership_id.membership_duration or 0

    @api.depends('extension_type', 'custom_days', 'new_membership_plan_id', 'same_plan_duration')
    def _compute_extension_details(self):
        """Compute extension days, new end date and amount"""
        for wizard in self:
            extension_days = 0
            extension_amount = 0.0

            if wizard.extension_type == 'same_plan':
                if wizard.membership_id.membership_scheme_id:
                    original_plan = wizard.membership_id.membership_scheme_id
                    if original_plan.membership_date_from and original_plan.membership_date_to:
                        extension_days = (original_plan.membership_date_to - original_plan.membership_date_from).days
                        extension_amount = original_plan.list_price

            elif wizard.extension_type == 'custom_days':
                extension_days = wizard.custom_days
                if wizard.membership_id.membership_scheme_id and extension_days > 0:
                    original_plan = wizard.membership_id.membership_scheme_id
                    if original_plan.membership_date_from and original_plan.membership_date_to:
                        original_days = (original_plan.membership_date_to - original_plan.membership_date_from).days
                        if original_days > 0:
                            daily_rate = original_plan.list_price / original_days
                            extension_amount = daily_rate * extension_days

            elif wizard.extension_type == 'new_plan':
                if wizard.new_membership_plan_id:
                    new_plan = wizard.new_membership_plan_id
                    if new_plan.membership_date_from and new_plan.membership_date_to:
                        extension_days = (new_plan.membership_date_to - new_plan.membership_date_from).days
                        extension_amount = new_plan.list_price

            wizard.extension_days = extension_days
            wizard.extension_amount = extension_amount

            if wizard.current_end_date and extension_days > 0:
                wizard.new_end_date = wizard.current_end_date + timedelta(days=extension_days)
            else:
                wizard.new_end_date = wizard.current_end_date

    @api.onchange('new_membership_plan_id')
    def _onchange_new_membership_plan_id(self):
        """Update new plan duration when plan changes"""
        if self.new_membership_plan_id:
            plan = self.new_membership_plan_id
            if plan.membership_date_from and plan.membership_date_to:
                self.new_plan_duration = (plan.membership_date_to - plan.membership_date_from).days

    def action_extend_membership(self):
        """Process the membership extension"""
        self.ensure_one()

        if self.extension_days <= 0:
            raise UserError(_('Extension days must be greater than 0.'))

        if self.extension_amount <= 0:
            raise UserError(_('Extension amount must be greater than 0.'))

        sale_order = self._create_extension_sale_order()

        self.membership_id.complete_extension(
            days_extended=self.extension_days,
            extension_amount=self.extension_amount,
            sale_order_id=sale_order.id
        )

        if self.extension_type == 'new_plan' and self.new_membership_plan_id:
            self.membership_id.membership_scheme_id = self.new_membership_plan_id.id

        return {
            'name': _('Extension Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_extension_sale_order(self):
        """Create sale order for membership extension"""
        if self.extension_type == 'new_plan' and self.new_membership_plan_id:
            product = self.new_membership_plan_id
            product_name = f"Extension - {product.name}"
        else:
            product = self.membership_id.membership_scheme_id
            if self.extension_type == 'same_plan':
                product_name = f"Extension - {product.name}"
            else:
                product_name = f"Extension - {self.extension_days} days"

        sale_order_vals = {
            'partner_id': self.member_id.id,
            'date_order': fields.Datetime.now(),
            'origin': f'Extension of {self.membership_id.reference}',
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': product_name,
                'product_uom_qty': 1,
                'price_unit': self.extension_amount,
            })]
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)
        return sale_order