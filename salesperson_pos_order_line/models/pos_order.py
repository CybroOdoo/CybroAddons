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


class PosOrderLine(models.Model):
    """Inherit pos.order.line to add salesperson."""
    _inherit = 'pos.order.line'

    user_id = fields.Many2one('res.users', string='Salesperson',
                              help="Salesperson assigned to this order line.")

    @api.model
    def _load_pos_data_fields(self, config):
        """Load field to pos."""
        params = super()._load_pos_data_fields(config)
        params += ['user_id']
        return params


class PosOrder(models.Model):
    """Inherit pos.order to handle salesperson on lines."""
    _inherit = 'pos.order'

    def _prepare_order_line(self, line):
        """Add the user_id field from the given line data."""
        res = super()._prepare_order_line(line) if hasattr(super(), '_prepare_order_line') else {}
        res['user_id'] = line.get('user_id')
        return res
