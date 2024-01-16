# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
        This class inherits from the `res.config.settings` model in Odoo and adds two
        boolean fields to the configuration settings page: `create_invoice_delivery_validate`
        and auto_send_invoice`. """
    _inherit = "res.config.settings"

    is_create_invoice_delivery_validate = fields.Boolean(
        string="Auto Post invoice",
        config_parameter='automatic_invoice_and_post.is_create_invoice_delivery_validate',
        help="If set to true, the invoice will automatically created.")
    is_auto_send_invoice = fields.Boolean(
        string="Auto Send Invoice",
        config_parameter='automatic_invoice_and_post.is_auto_send_invoice',
        help="If set to true, the invoice will "
             "automatically send to the customer.")
