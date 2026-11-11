#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inheriting pos.order to store whether it is a Take Away order and its
    token number."""
    _inherit = 'pos.order'

    is_takeaway = fields.Boolean(
        string="Is a Take Away Order",
        help="Orders that are not Take Away are Dine-In orders",
    )
    takeaway_token = fields.Integer(
        string="Take Away Token",
        help="Token number issued for this Take Away order",
        readonly=True,
        copy=False,
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Make sure the Take Away fields are loaded in the POS frontend."""
        fields_list = super()._load_pos_data_fields(config)
        if fields_list:
            fields_list += [
                name for name in ('is_takeaway', 'takeaway_token')
                if name not in fields_list]
        return fields_list

    def _assign_takeaway_token(self):
        """Give a token to Take Away orders that do not have one yet."""
        for order in self:
            config = order.session_id.config_id
            if (order.is_takeaway and not order.takeaway_token
                    and config.is_generate_token):
                order.takeaway_token = config._get_next_takeaway_token()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._assign_takeaway_token()
        return orders

    def write(self, vals):
        if 'is_takeaway' in vals and not vals['is_takeaway']:
            vals = dict(vals, takeaway_token=0)
        res = super().write(vals)
        if vals.get('is_takeaway'):
            self._assign_takeaway_token()
        return res
