# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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
################################################################################

from odoo import fields, models


class SaleOrder(models.Model):
    """Class to add the field in sale order"""
    _inherit = 'sale.order'

    agent_id = fields.Many2one(
        'res.partner', 'Agent',
        help='Select a agent for the customer')

    def _prepare_invoice(self):
        """Function to update the agent_id field in invoice based on the sale
        order"""
        res = super()._prepare_invoice()
        res['agent_id'] = self.agent_id.id
        return res
