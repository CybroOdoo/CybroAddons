# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import requests
from countryinfo import CountryInfo
from odoo import models


class Website(models.Model):
    """ Class for selecting shop's public pricelist """
    _inherit = 'website'

    def get_user_location(self):
        """ Get location details of user """
        response = requests.get(
            f'http://ip-api.com/json/{self.env.user.ip_address}', timeout=20).json()
        return {"country": response.get("country")}

    def _get_current_pricelist(self):
        """ Get current pricelist if it is public pricelist then
            change its currency into customers currency """
        res = super()._get_current_pricelist()
        default = self.env['product.pricelist'].search([])
        if res in default:
            datas = self.get_user_location()
            if datas:
                country = CountryInfo(datas['country'])
                currency = country.currencies()
                currency_dict = self.env['res.currency'].sudo().search([
                    ('name', '=', currency[0]),
                    ('active', 'in', [True, False])])
                if currency_dict:
                    currency_dict.active = True
                    res.currency_id = currency_dict
        return res
