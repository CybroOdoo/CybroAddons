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


class RecruitmentSettings(models.TransientModel):
    _inherit = 'hr.recruitment.config.settings'

    company_page_id = fields.Char(string="Company Page ID", help="")
    li_username = fields.Char(string="User Name", help="")
    li_password = fields.Char(string="Password", help="")


    @api.multi
    def set_linkedin_page_id(self):
        """ Set function for LinkedIn credentials """
        return self.env['ir.values'].sudo().set_default(
            'hr.recruitment.config.settings', 'company_page_id', self.company_page_id)

    @api.multi
    def set_linkedin_username(self):
        """ Set function for LinkedIn credentials """
        return self.env['ir.values'].sudo().set_default(
            'hr.recruitment.config.settings', 'li_username', self.li_username)

    @api.multi
    def set_linkedin_pw(self):
        """ Set function for LinkedIn credentials """
        return self.env['ir.values'].sudo().set_default(
            'hr.recruitment.config.settings', 'li_password', self.li_password)



