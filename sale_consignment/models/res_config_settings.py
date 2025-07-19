# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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

################################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ This transient model is used to add the custom fields to the
    settings page. """
    _inherit = 'res.config.settings'

    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        help="Location where you want to send the components resulting "
             "from the un-build order.",
        config_parameter='sale_consignment.location_dest_id',
        readonly=False)
    group_consignment_order = fields.Boolean(
        string='Consignment', readonly=False, default=True,
        config_parameter='sale_consignment.group_consignment_order',
        help="Consignment Orders",
        implied_group='sale_consignment.group_consignment_order')
    consignment_product_only = fields.Boolean(
        string='Consignment Product',
        config_parameter='sale_consignment.consignment_product_only',
        help='Enable Product Filtered in consignment by Consignment Product')
    consignment_customer_only = fields.Boolean(
        string='Consignment Customer',
        config_parameter='sale_consignment.consignment_customer_only',
        help='Enable Customer Filtered in consignment by Consignment Customer')
