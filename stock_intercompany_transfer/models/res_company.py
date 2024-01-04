# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class ResCompany(models.Model):
    """Inherits 'res.company' and adds fields"""
    _inherit = 'res.company'

    enable_inter_company_transfer = fields.Boolean(string='Inter Company '
                                                          'Transfer',
                                                   copy=False,
                                                   help="Enable/disable inter "
                                                        "company transfer to"
                                                        "select "
                                                        "delivery/receipts.")
    destination_warehouse_id = fields.Many2one('stock.warehouse',
                                               string='Warehouse',
                                               help="Select the destination"
                                                    " warehouse of the"
                                                    " company.")
    apply_transfer_type = fields.Selection([('all', 'Delivery and '
                                                    'Receipts'),
                                            ('incoming', 'Receipt'),
                                            ('outgoing', 'Delivery Order')],
                                           string='Apply On',
                                           default='all',
                                           help="Select the Picking type to "
                                                "apply the inter "
                                                "company transfer.")
    message = fields.Text(string="Message", compute='compute_message',
                          help="Message shown on selecting the type "
                               "of orders.")

    @api.depends('apply_transfer_type', 'destination_warehouse_id')
    def compute_message(self):
        """Creating the Display message according to the selected type."""
        for rec in self:
            if rec.apply_transfer_type == 'incoming':
                create_type = "Delivery"
                selected_type = "Receipt"
            elif rec.apply_transfer_type == 'outgoing':
                create_type = "Receipt"
                selected_type = "Delivery"
            else:
                create_type = "Delivery Order/Receipt"
                selected_type = "Receipt/Delivery"

            msg = _("Create a %s Order when a company validate a "
                    "%s Order for %s using %s Warehouse.") % (create_type,
                                                              selected_type,
                                                              rec.sudo().name,
                                                              rec.sudo().destination_warehouse_id.name)
            rec.message = msg

    @api.onchange('enable_inter_company_transfer')
    def onchange_inter_company_transfer(self):
        """Function to execute on changing the boolean field Inter Company
        transfer to search for the warehouse"""
        company = self._origin
        wh = self.env['stock.warehouse'].sudo().search([('company_id', '=',
                                                         company.sudo().id)],
                                                       limit=1, order='id ASC')
        self.destination_warehouse_id = wh
