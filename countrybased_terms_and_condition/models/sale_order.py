# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import api, models


class SalesOrder(models.Model):
    """
This class extends the Sale Order model to include custom fields and methods.
    """
    _inherit = "sale.order"

    @api.depends('partner_id')
    def _compute_note(self):
        """
        Compute the value of the 'note' field for the current record based
        on the value of the 'partner_id' field. If the country associated
        with the partner has a value for 'sale_terms_condition', use that
        value as the note. Otherwise, call the parent method to compute the
        value.
        """
        terms_and_condition = self.partner_id.country_id.sale_terms_condition
        if terms_and_condition:
            self.note = terms_and_condition
        else:
            res = super(SalesOrder, self)._compute_note()
            return res
