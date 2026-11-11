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


class PosConfiguration(models.Model):
    """ Declaring the class for POS Configuration and adding fields in POS
    config """
    _inherit = 'pos.config'

    is_pos_takeaway = fields.Boolean(
        string='POS Take Away',
        help='Enable Take Away and Dine-In orders in the restaurant POS',
    )
    is_generate_token = fields.Boolean(
        string='Generate Token',
        help='Generate a token number for Take Away orders',
    )
    pos_token = fields.Integer(
        string="Token Number",
        help="Last token number issued by this POS. The next token is this "
             "number plus one, starting from 1.",
        readonly=True,
        copy=False,
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Make sure the Take Away fields are loaded in the POS frontend."""
        fields_list = super()._load_pos_data_fields(config)
        if fields_list:
            fields_list += [
                name for name in ('is_pos_takeaway', 'is_generate_token',
                                  'pos_token') if name not in fields_list]
        return fields_list

    def _get_next_takeaway_token(self):
        """Atomically increment and return the token of this POS."""
        self.ensure_one()
        self.env.cr.execute(
            "UPDATE pos_config SET pos_token = COALESCE(pos_token, 0) + 1 "
            "WHERE id = %s RETURNING pos_token", (self.id,))
        token = self.env.cr.fetchone()[0]
        self.invalidate_recordset(['pos_token'])
        return token
