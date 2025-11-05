# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018-TODAY NIKHIL KRISHNAN(nikhilkrishnan0101@gmail.com).
#    Author: Nikhil krishnan(nikhilkrishnan0101@gmail.com)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    so_expiration_date = fields.Selection([('0', "No Default Expiration Date"), ('1', "Default 14 days"),
                                           ('2', 'Created as company rule')], "Expiration Date",
                                          default='0', help="Allows you to set Expiration Date.")
    so_expiration_date_start = fields.Selection([('0', "Quotation Creation Date"),
                                                 ('1', "Quotation Sent Date")],
                                                "Expiration Date Start from", default='0',
                                                help="Allows you to set Expiration Date Start from.")
    so_expiration_date_no = fields.Integer(string="No.of Days")

    @api.model
    def get_values(self):
        res = super(SaleConfiguration, self).get_values()
        a = self.env['ir.config_parameter'].sudo().get_param('quotation_handler.so_expiration_date_no')
        res.update(
            so_expiration_date=self.env['ir.config_parameter'].sudo().get_param('quotation_handler.so_expiration_date'),
            so_expiration_date_start=self.env['ir.config_parameter'].sudo().get_param('quotation_handler.so_expiration_date_start'),
            so_expiration_date_no=int(a)
        )
        return res

    @api.multi
    def set_values(self):
        super(SaleConfiguration, self).set_values()
        a = self.so_expiration_date
        print("type", type(a))
        if a == '0':
            so_expiration_date_nos = False
        elif a == '1':
            so_expiration_date_nos = 14
        else:
            so_expiration_date_nos = self.so_expiration_date_no
        self.env['ir.config_parameter'].sudo().set_param('quotation_handler.so_expiration_date', self.so_expiration_date)
        self.env['ir.config_parameter'].sudo().set_param('quotation_handler.so_expiration_date_start', self.so_expiration_date_start)
        self.env['ir.config_parameter'].sudo().set_param('quotation_handler.so_expiration_date_no', int(so_expiration_date_nos))
