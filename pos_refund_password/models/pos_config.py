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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PosConfig(models.Model):
    """Inherit POS configuration to add refund password security."""
    _inherit = 'pos.config'

    refund_security = fields.Char(
        string='Refund Password',
        groups='point_of_sale.group_pos_manager',
        help="Password required to authorize refunds for this Point of Sale.",
    )
    has_refund_password = fields.Boolean(
        compute='_compute_has_refund_password',
        compute_sudo=True,
        help="Technical field indicating if a refund password is configured.",
    )

    @api.depends('refund_security')
    def _compute_has_refund_password(self):
        """Check if global or POS-specific refund password is configured."""
        global_security = self.env['ir.config_parameter'].sudo().get_str(
            'pos_refund_password.global_refund_security', default='',
        )
        for config in self:
            config.has_refund_password = bool(
                global_security or config.sudo().refund_security,
            )

    @api.model
    def _load_pos_data_read(self, records, config):
        """Include has_refund_password in POS configuration data."""
        read_records = super()._load_pos_data_read(records, config)
        if read_records:
            read_records[0]['has_refund_password'] = (
                config.sudo().has_refund_password
            )
        return read_records

    def verify_refund_password(self, password):
        """Verify the entered refund password.
        The global password overrides the POS-specific password if set.
        """
        self.ensure_one()
        global_pass = self.env['ir.config_parameter'].sudo().get_str(
            'pos_refund_password.global_refund_security', default='',
        )
        expected_pass = global_pass or self.sudo().refund_security
        if not expected_pass:
            return True
        return bool(
            password and str(password).strip() == str(expected_pass).strip(),
        )
