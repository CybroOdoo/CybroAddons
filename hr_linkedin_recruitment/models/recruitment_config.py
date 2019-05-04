# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Author: Nilmar Shereef (<shereef@cybrosys.in>)
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
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
###################################################################################
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    li_username = fields.Char(string="User Name", help="Your Linkedin Username")
    li_password = fields.Char(string="Password", help="Your Linkedin Password")

    def set_values(self):

        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('recruitment.company_page_id', self.company_page_id)
        self.env['ir.config_parameter'].sudo().set_param('recruitment.li_username', self.li_username)
        self.env['ir.config_parameter'].sudo().set_param('recruitment.li_password', self.li_password)

    def get_values(self):
            res = super(ResConfigSettings, self).get_values()
            res.update(
                company_page_id=self.env['ir.config_parameter'].sudo().get_param('recruitment.company_page_id'),
                li_username = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_username'),
                li_password = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_password')
            )
            return res




