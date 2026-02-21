# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """This class represents the order of samples in the sale order"""
    _inherit = 'sale.order'

    is_sample_order = fields.Boolean(string="Sample order",
                                     help="To identify as a sample order")

    @api.model
    def create(self, vals):
        """
        Override create to ensure that when a sale order is created through
        the 'Sample Orders' action, the 'is_sample_order' field is automatically
        set to True via context.
        """
        if self._context.get('default_is_sample_order'):
            vals['is_sample_order'] = True
        else:
            vals.setdefault('is_sample_order', False)  # ensure False if not set
        return super().create(vals)
