# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
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
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    """This transient model is used to add the custom fields to the 
    settings page"""

    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        help="Location where you want to send the components resulting "
             "from the un-build order.",
        required=True,
        config_parameter='sale_consignment.location_dest_id',
        readonly=False)
    group_consignment_order = fields.Boolean(string='Consignment',
                                             readonly=False,
                                             default=True,
                                             config_parameter='sale_consignment.group_consignment_order',
                                             implied_group='sale_consignment.group_consignment_order')
    consignment_product_only = fields.Boolean(help='Enable Product '
                                                   'Filtered in '
                                                   'consignment by '
                                                   'Consignment Prodduct',
                                              string='Consignment Product',
                                              config_parameter='sale_consignment.consignment_product_only', )
    consignment_customer_only = fields.Boolean(help='Enable Customer '
                                                    'Filtered in '
                                                    'consignment by '
                                                    'Consignment Customer',
                                               string='Consignment Customer',
                                               config_parameter='sale_consignment.consignment_customer_only', )
