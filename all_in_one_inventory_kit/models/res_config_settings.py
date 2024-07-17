# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherits res.config.settings """
    _inherit = 'res.config.settings'

    customer_journal_id = fields.Many2one(
        'account.journal',
        string='Customer Journal',
        config_parameter='stock_move_invoice.customer_journal_id',
        help="Customer journals")
    vendor_journal_id = fields.Many2one(
        'account.journal',
        string='Vendor Journal',
        config_parameter='stock_move_invoice.vendor_journal_id',
        help="Vendor journals")
    out_of_stock = fields.Boolean(
        string="Out Of Stock",
        config_parameter='all_in_one_inventory_kit.out_of_stock',
        help="Is out of stock")
    out_of_stock_quantity = fields.Integer(
        string="Quantity",
        config_parameter='all_in_one_inventory_kit.out_of_stock_quantity',
        required=True,
        help="Out of stock quantity")
    dead_stock_bol = fields.Boolean(
        string="Dead Stock",
        config_parameter='all_in_one_inventory_kit.dead_stock_bol',
        help="Is this is a dead stock")
    dead_stock = fields.Integer(
        config_parameter='all_in_one_inventory_kit.dead_stock',
        required=True, help="Dead stock")
    dead_stock_type = fields.Selection(
        [('day', 'Day'), ('week', 'Week'), ('month', 'Month')],
        string="Type", default='day',
        config_parameter='all_in_one_inventory_kit.dead_stock_type',
        required=True, help="Dead stock type")
