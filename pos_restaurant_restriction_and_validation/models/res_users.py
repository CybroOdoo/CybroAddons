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


class ResUsers(models.Model):
    """
    Inherits res.users to store the POS security PIN for manager level approvals.
    """
    _inherit = 'res.users'

    pos_security_pin = fields.Char(
        string="POS Security PIN",
        groups="point_of_sale.group_pos_manager",
        copy=False,
        help="PIN used for manager approval in POS"
    )
    pos_pin_failed_attempts = fields.Integer(
        string="POS PIN Failed Attempts",
        copy=False,
        default=0,
        groups="point_of_sale.group_pos_manager",
        help="Number of consecutive failed PIN verification attempts"
    )
    pos_pin_lockout_until = fields.Datetime(
        string="POS PIN Lockout Until",
        copy=False,
        groups="point_of_sale.group_pos_manager",
        help="Lockout expiration time if too many failed attempts occur"
    )

    @api.model
    def _pin_crypt_context(self):
        """Returns a salted PBKDF2-SHA512 CryptContext without plaintext fallback."""
        ctx = self._crypt_context().copy()
        ctx.update(schemes=['pbkdf2_sha512'])
        return ctx

    @api.model
    def _hash_pin(self, pin):
        """Hashes a PIN string using salted PBKDF2-SHA512."""
        if not pin:
            return False
        pin_str = str(pin).strip()
        if not pin_str:
            return False
        return self._pin_crypt_context().hash(pin_str)

    def check_pos_security_pin(self, candidate_pin):
        """Verifies candidate PIN against the stored PBKDF2-SHA512 hash."""
        self.ensure_one()
        if not self.pos_security_pin or not candidate_pin:
            return False
        pin_str = str(candidate_pin).strip()
        if not pin_str:
            return False
        ctx = self._pin_crypt_context()
        if ctx.identify(self.pos_security_pin) != 'pbkdf2_sha512':
            return False
        return ctx.verify(pin_str, self.pos_security_pin)

    @api.model_create_multi
    def create(self, vals_list):
        sanitized_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get('pos_security_pin'):
                vals['pos_security_pin'] = self._hash_pin(vals['pos_security_pin'])
            sanitized_vals_list.append(vals)
        return super().create(sanitized_vals_list)

    def write(self, vals):
        if 'pos_security_pin' in vals and vals['pos_security_pin']:
            vals = dict(vals)
            vals['pos_security_pin'] = self._hash_pin(vals['pos_security_pin'])
        return super().write(vals)

