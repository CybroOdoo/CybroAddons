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
    set_opening_hours = fields.Boolean(string="Set Opening Hours",
                                       help="Enable to configure restaurant opening and closing hours.",
                                       config_parameter="table_"
                                                        "reservation_on_"
                                                        "website.reservation"
                                                        "set_opening_hours")
    opening_hour = fields.Float(string="Opening Hours",
                                help="Restaurant opening hour in 24-hour format."
                                )
    closing_hour = fields.Float(string="Closing Hours",
                                help="Restaurant closing hour in 24-hour format."
                                )

    def set_values(self):
        """To set the value for a fields in config setting"""
        """To set the value for fields in config setting"""
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('table_reservation_on_website.refund',
                         self.refund or "")
        params.set_param('table_reservation_on_website.opening_hour',
                         self.opening_hour or 0.0)
        params.set_param('table_reservation_on_website.closing_hour',
                         self.closing_hour or 0.0)

    def get_values(self):
        """To get the values in config settings"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        res.update(
            refund=params.get_param('table_reservation_on_website.refund', ""),
            opening_hour=float(params.get_param('table_reservation_on_website.opening_hour', 0.0)),
            closing_hour=float(params.get_param('table_reservation_on_website.closing_hour', 0.0))
        )
        return res

