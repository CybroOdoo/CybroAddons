# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Used to add new fields to the settings"""
    _inherit = "res.config.settings"

    customer_details = fields.Boolean(
        related='pos_config_id.customer_details',
        string=" Customer Details",
        help="By Enabling the customer details"
             " in pos receipt",
        readonly=False
    )
    customer_name = fields.Boolean(
        related='pos_config_id.customer_name',
        string=" Customer Name",
        help="By Enabling the customer name "
             "in pos receipt",
        readonly=False
    )
    customer_address = fields.Boolean(
        related='pos_config_id.customer_address',
        string=" Customer Address",
        help="By Enabling the customer Address "
             "in pos receipt",
        readonly=False
    )
    customer_mobile = fields.Boolean(
        related='pos_config_id.customer_mobile',
        string=" Customer Mobile",
        help="By Enabling the customer mobile "
             "in pos receipt",
        readonly=False
    )
    customer_phone = fields.Boolean(
        related='pos_config_id.customer_phone',
        string=" Customer Phone",
        help="By Enabling the customer phone "
             "in pos receipt",
        readonly=False
    )
    customer_email = fields.Boolean(
        related='pos_config_id.customer_email',
        string=" Customer Email",
        help="By Enabling the customer email "
             "in pos receipt",
        readonly=False
    )
    customer_vat = fields.Boolean(
        related='pos_config_id.customer_vat',
        string=" Customer Vat",
        help="By Enabling the customer vat details "
             "in pos receipt",
        readonly=False
    )
