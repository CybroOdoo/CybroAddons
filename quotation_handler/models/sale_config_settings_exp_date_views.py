# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    so_expiration_date = fields.Selection([(0, "No Default Expiration Date"), (1, "Default 14 days"),
                                           (2, 'Created as company rule')], "Expiration Date",
                                          help="Allows you to set Expiration Date.")
    so_expiration_date_start = fields.Selection([(0, "Quotation Creation Date"),
                                                 (1, "Quotation Sent Date")],
                                                "Expiration Date Start from",
                                                help="Allows you to set Expiration Date Start from.")
    so_expiration_date_no = fields.Integer(string="No.of Days")

    @api.multi
    def set_default_so_expiration_date(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'so_expiration_date', self.so_expiration_date)

    @api.multi
    def set_default_so_expiration_date_start(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'so_expiration_date_start', self.so_expiration_date_start)

    @api.multi
    def set_default_so_expiration_date_no(self):
        a = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date', self.so_expiration_date)
        if a == 0:
            so_expiration_date_no = False
        elif a == 1:
            so_expiration_date_no = 14
        else:
            so_expiration_date_no = self.so_expiration_date_no
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'so_expiration_date_no', so_expiration_date_no)


