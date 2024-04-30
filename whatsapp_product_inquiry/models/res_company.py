# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.

###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    """Inherits Company for Adding the Whatsapp Fields"""
    _inherit = 'res.company'

    whatsapp_number = fields.Char(string='Whatsapp Number',
                                  help="The Company Whatsapp Number to "
                                       "which the Inquiry messages has to"
                                       " be received")
    message = fields.Text(string='Message',
                          default="I want to know more details of the product",
                          help="This will be the Inquiry message")

    @api.constrains('whatsapp_number')
    def _check_whatsapp_number(self):
        """Validate Mobile Number"""
        if self.whatsapp_number:
            if not self.whatsapp_number.isnumeric() or not len(
                    self.whatsapp_number) > 8 or ' ' in self.whatsapp_number:
                raise UserError(_('Whatsapp Number should be valid number'
                                  ' without any space or signs'))
