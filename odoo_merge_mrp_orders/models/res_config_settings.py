#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Roopchand P M(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherit the settings to add options to enable additional features
     for merging manufacturing order."""
    _inherit = 'res.config.settings'

    merge_mrp_type = fields.Selection(
        string="Merge Type",
        selection=[
            ('order_none', "New order and Do nothing with selected mrp orders"),
            ('order_cancel', "New order and Cancel selected mrp orders"),
            ('order_remove', "New order and Remove selected mrp orders"),
            ('merge_none',
             "Existing order and Do nothing with selected mrp orders"),
            ('merge_cancel', "Existing order and Cancel selected mrp orders"),
            ('merge_remove', "Existing order and Remove selected mrp orders")
        ],
        default='order_none',
        config_parameter='odoo_merge_mrp_orders.merge_mrp_type',
        help="Select the type of merge operation for manufacturing orders."
    )
    merge_order_notify = fields.Boolean(
        string='Notify in chatter',
        config_parameter='odoo_merge_mrp_orders.merge_order_notify',
        help="Enable notification in the chatter for merged manufacturing "
             "orders.")
    merge_qty = fields.Boolean(
        string="Manage merge quantity",
        config_parameter='odoo_merge_mrp_orders.merge_qty',
        help="Enable managing merge quantity for merged manufacturing orders.")
