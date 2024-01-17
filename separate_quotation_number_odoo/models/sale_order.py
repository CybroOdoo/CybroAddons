# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
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
from odoo import api, fields, models


class SaleOrder(models.Model):
    """
    This class extends the default 'sale.order' model to include an additional
    field called 'quotation_ref', which holds an auto-generated reference
    number for the quotation.
    """
    _inherit = 'sale.order'

    quotation_ref = fields.Char(string='Quotation Reference',
                                copy=False, readonly=True, tracking=True,
                                help="Auto-generated reference number")

    @api.model_create_multi
    def create(self, vals):
        """
        Create Sale Orders and generate sequence numbers for quotations.
        This method is called when creating multiple sale orders at once.
        Generates a unique sequence number for each sale order's 'quotation_ref'
        field using the 'seq_quotation'.

        :param vals_list: A list of dictionaries containing values for creating
                            multiple sale orders.
        :type vals_list: list(dict)
        :return: The created sale orders.
        """
        res = super(SaleOrder, self).create(vals)
        for vals in res:
            seq_val = self.env.ref(
                'separate_quotation_number_odoo.seq_quotation').id
            vals.quotation_ref = self.env['ir.sequence'].browse(
                seq_val).next_by_id()
        return res
