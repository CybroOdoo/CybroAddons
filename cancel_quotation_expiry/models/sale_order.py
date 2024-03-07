# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
###############################################################################
from datetime import date
from odoo import models


class SaleOrder(models.Model):
    """Inherit Sale Order to add functionality for canceling expired
    quotations."""
    _inherit = 'sale.order'

    def cancel_expired_quotation(self):
        """Automatically cancel the expired quotations."""
        expired_quotation = self.search([('state', 'in', ['draft', 'sent']),
                                         ('validity_date', '<', date.today())])
        if expired_quotation:
            for rec in expired_quotation:
                rec.action_cancel()
