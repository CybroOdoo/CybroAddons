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
from datetime import timedelta
from odoo import api, fields, models


class PosConfig(models.Model):
    """
    Inherits pos.config to add restricted action configuration fields.
    """
    _inherit = 'pos.config'

    pos_restaurant_restriction = fields.Boolean(
        string="Restaurant Restriction",
        help="Enable restriction on some operations once the order has been sent to the kitchen"
    )
    pos_orderline_quantity_update = fields.Boolean(
        string="Orderline Quantity Update",
        help="Require manager approval to update orderline quantity"
    )
    pos_orderline_delete = fields.Boolean(
        string="Orderline Delete",
        help="Require manager approval to delete an orderline"
    )
    pos_order_delete = fields.Boolean(
        string="Order Delete",
        help="Require manager approval to delete an order"
    )
    pos_session_close = fields.Boolean(
        string="Session Close",
        help="Require manager approval to close the POS session"
    )

    @api.model
    def _load_pos_data_read(self, records, config):
        """
        Extends loading process to include custom restriction fields in the POS frontend.
        """
        res = super()._load_pos_data_read(records, config)
        for record in res:
            config_rec = self.browse(record['id'])
            record.update({
                'pos_restaurant_restriction': config_rec.pos_restaurant_restriction,
                'pos_orderline_quantity_update': config_rec.pos_orderline_quantity_update,
                'pos_orderline_delete': config_rec.pos_orderline_delete,
                'pos_order_delete': config_rec.pos_order_delete,
                'pos_session_close': config_rec.pos_session_close,
            })
        return res

    def is_restriction_authorized(self, action_type, order_ref=False, product_id=False, consume=True):
        """Checks if current user has manager approval or bypass rights for restricted action."""
        if self.env.user.has_group('point_of_sale.group_pos_manager') or self.env.su:
            return True
        if self.env.context.get('pos_restriction_approved'):
            return True
        time_limit = fields.Datetime.now() - timedelta(minutes=10)
        domain = [
            ('action_type', '=', action_type),
            ('is_consumed', '=', False),
            ('create_date', '>=', time_limit),
            ('user_id', '=', self.env.user.id),
        ]
        if action_type == 'session_close':
            if not order_ref:
                return False
            domain.append(('order_ref', '=', order_ref))
        else:
            if order_ref:
                domain.append(('order_ref', '=', order_ref))
            if product_id:
                domain.append(('product_id', '=', product_id))

        log = self.env['pos.action.log'].sudo().search(domain, limit=1)
        if log:
            if consume:
                log.sudo().write({'is_consumed': True})
            return True
        return False

    @api.model
    def get_managers_for_approval(self, config_id=False):
        """
        Returns a list of managers (users in POS Manager group with PIN set)
        eligible for approvals. Sudo is used so non-manager cashiers do not
        encounter AccessError on pos_security_pin.
        """
        _ = config_id
        managers = []
        pos_manager_group = self.sudo().env.ref(
            'point_of_sale.group_pos_manager', raise_if_not_found=False
        )
        if pos_manager_group:
            for user in pos_manager_group.sudo().user_ids.filtered(lambda u: u.active):
                if user.sudo().pos_security_pin:
                    managers.append({'id': user.id, 'name': user.name})

        return managers

    def _handle_failed_pin_attempt(self, caller):
        """Records failed PIN attempt on the caller and triggers lockout after threshold."""
        if not (caller and caller.exists()):
            return
        now = fields.Datetime.now()
        max_attempts = 5
        lockout_duration = timedelta(minutes=5)

        caller_sudo = caller.sudo()
        attempts = (caller_sudo.pos_pin_failed_attempts or 0) + 1
        vals = {'pos_pin_failed_attempts': attempts}
        if attempts >= max_attempts:
            vals['pos_pin_lockout_until'] = now + lockout_duration
            vals['pos_pin_failed_attempts'] = 0
        caller_sudo.write(vals)

    @api.model
    def validate_manager_pin_for_restriction(
        self, config_id, manager_id, pin, action_type,
        product_id=False, old_qty=0.0, new_qty=0.0, order_ref=False,
        cashier_user_id=False, cashier_name=False
    ):
        """
        Validates the manager's PIN for a restricted action, rate-limits attempts
        per caller, and creates an audit log entry.
        Guards against spoofing of cashier user identity and verifies hashed PIN.
        """
        _ = config_id
        manager = self.sudo().env['res.users'].browse(manager_id)
        caller = self.env.user.sudo()
        now = fields.Datetime.now()

        # Check rate-limiting / lockout keyed on the caller (never lock out the manager globally)
        if caller.exists() and caller.pos_pin_lockout_until and caller.pos_pin_lockout_until > now:
            return {
                'approved': False,
                'locked': True,
                'error': self.env._("Too many failed attempts. Your account is temporarily locked from requesting approval.")
            }

        # Check PIN presence and manager eligibility
        if not pin or not str(pin).strip():
            return {'approved': False}

        if not (
            manager.exists()
            and manager.has_group('point_of_sale.group_pos_manager')
            and manager.sudo().pos_security_pin
            and manager.sudo().check_pos_security_pin(str(pin).strip())
        ):
            self._handle_failed_pin_attempt(caller)
            return {'approved': False}

        # Successful PIN validation: reset caller failure counters if set
        if caller.pos_pin_failed_attempts or caller.pos_pin_lockout_until:
            caller.write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})

        # Anti-spoofing for cashier identity:
        # A regular cashier cannot spoof cashier_user_id or cashier_name.
        # Only managers or superusers may specify an explicit cashier identity.
        is_manager_or_su = self.env.su or self.env.user.has_group('point_of_sale.group_pos_manager')
        if is_manager_or_su and cashier_user_id:
            resolved_user = self.sudo().env['res.users'].browse(cashier_user_id)
            user_id = resolved_user.id if resolved_user.exists() else self.env.user.id
            resolved_cashier_name = cashier_name or (resolved_user.name if resolved_user.exists() else self.env.user.name)
        else:
            user_id = self.env.user.id
            resolved_cashier_name = self.env.user.name

        # Create audit log using sudo
        self.env['pos.action.log'].sudo().create({
            'user_id': user_id,
            'cashier_name': resolved_cashier_name,
            'action_type': action_type,
            'approved_by': manager.id,
            'order_ref': order_ref or False,
            'product_id': product_id if product_id else False,
            'old_qty': old_qty,
            'new_qty': new_qty,
            'is_consumed': False,
        })
        return {'approved': True}

