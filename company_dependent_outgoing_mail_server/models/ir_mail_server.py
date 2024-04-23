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
from odoo import api, fields, models


class IrMailServer(models.Model):
    """Inherited ir.mail_server and added a company dependent field"""
    _inherit = 'ir.mail_server'
    _description = 'Added a company dependent field in ir.mail_server'

    company_id = fields.Many2one('res.company', string='Company',
                                 help='Specify this if you want company '
                                      'dependent out going mail server')

    def _find_mail_server(self, email_from, mail_servers=None):
        """Function which finds appropriate outgoing email server for current
        company"""
        mail_server = self.env['ir.mail_server'].search([
            (
                'company_id.id', '=',
                self.env['ir.config_parameter'].sudo().get_param(
                    'current.company.id'))
        ],
            order='sequence asc', limit=1)
        res = super()._find_mail_server(email_from)
        lst = list(res)
        lst[0] = mail_server
        res = tuple(lst)
        return res

    @api.model
    def get_company_id(self, current_company):
        """Function called from orm and has current company id in argument"""
        self.env['ir.config_parameter'].sudo().set_param('current.company.id',
                                                         current_company)
