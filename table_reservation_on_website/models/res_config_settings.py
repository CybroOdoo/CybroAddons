# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
    """Inherit the model res config settings"""
    _inherit = 'res.config.settings'

    reservation_charge = fields.Boolean(string="Reservation Charge",
                                        help="Payment for pre booking tables",
                                        config_parameter="table_"
                                                         "reservation_on_"
                                                         "website.reservation"
                                                         "_charge")
    refund = fields.Text(string="No Refund Notes", help="No refund notes to "
                                                        "display in website")

    def set_values(self):
        """To set the value for a fields in config setting"""
        self.env['ir.config_parameter'].set_param(
            'table_reservation_on_website.refund', self.refund)
        return super(ResConfigSettings, self).set_values()

    def get_values(self):
        """To get the value in config settings"""
        res = super(ResConfigSettings, self).get_values()
        refund = self.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.refund')
        res.update(refund=refund if refund else False)
        return res
