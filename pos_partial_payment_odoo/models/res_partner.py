# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Athul Raj B S (odoo@cybrosys.info)
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
################################################################################
from odoo import api,fields, models


class ResPartner(models.Model):
    """
    This class extends the 'res.partner' model to introduce the 'prevent_partial_payment'
    field.
    """
    _inherit = 'res.partner'

    prevent_partial_payment = fields.Boolean(
        string="Don't allow Partial Payment in POS",
        help="If enabled, partial payments will be prevented for Point of Sale "
             "orders associated with this partner.")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Extend the fields to be loaded for 'res.partner' in the POS session to
        include the 'prevent_partial_payment' field.
        """
        data = super()._load_pos_data_fields(config_id)
        data += ['prevent_partial_payment']
        return data
