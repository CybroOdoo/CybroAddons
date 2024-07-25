# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Inheriting res config settings to add reservation details """
    _inherit = 'res.config.settings'

    reservation_charge = fields.Boolean(string="Reservation Charge",
                                        help="Payment for pre booking tables",
                                        config_parameter="table_"
                                                         "reservation_on_"
                                                         "website.reservation"
                                                         "_charge")
    refund = fields.Text(string="Notes",
                         help="You can display this notes in Website table "
                              "booking")
    is_lead_time = fields.Boolean(
        string="Lead Time",
        help="Enable to set lead time for reservations")
    reservation_lead_time = fields.Float(
        string="Reservation Lead Time",
        help="The order should be reserved hours"
             "before the booking start time.")

    def set_values(self):
        """ To set the value for fields in config setting """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'table_reservation_on_website.refund', self.refund)
        self.env['ir.config_parameter'].set_param(
            'table_reservation_on_website.is_lead_time', self.is_lead_time)
        self.env['ir.config_parameter'].sudo().set_param(
            'table_reservation_on_website.reservation_lead_time',
            self.reservation_lead_time)
        return res

    def get_values(self):
        """ To get the value in config settings """
        res = super(ResConfigSettings, self).get_values()
        refund = self.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.refund')
        res.update(refund=refund if refund else False)
        is_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.is_lead_time')
        res.update(is_lead_time=is_lead_time if is_lead_time else False)
        reservation_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.reservation_lead_time')
        res.update(
            reservation_lead_time=reservation_lead_time if reservation_lead_time
            else 0.0)
        return res
