# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import _, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    """Enforce the POS button restrictions on the server side."""
    _inherit = 'pos.order'

    def _process_order(self, order, existing_order):
        """Reject refund lines created by a user restricted from refunds."""
        if 'Refund' in self.env.user.sudo().buttons_pos_ids.mapped('name'):
            for command in order.get('lines') or []:
                if (isinstance(command, (list, tuple)) and len(command) == 3
                        and command[0] == 0
                        and isinstance(command[2], dict)
                        and command[2].get('refunded_orderline_id')):
                    raise UserError(_(
                        "You are not allowed to refund orders in the "
                        "Point of Sale."))
        return super()._process_order(order, existing_order)
