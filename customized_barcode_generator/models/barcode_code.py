# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError


class BarcodeCode(models.Model):
    """This class creates a model with needed fields"""
    _name = 'barcode.code'
    _description = 'Barcode Code'
    name = fields.Char(default='Numeric Code', help="Name of code.")
    code_for_zero = fields.Char(string=' 0 ', required=True, size=1,
                                default='a', help="insert substitute code. ")
    code_for_one = fields.Char(string='1 ', required=True, size=1,
                               default='b', help="insert substitute code. ")
    code_for_two = fields.Char(string='2 ', required=True,size=1,
                               default='c', help="insert substitute code.")
    code_for_three = fields.Char(string='3 ', required=True,size=1,
                                 default='d', help="insert substitute code. ")
    code_for_four = fields.Char(string='4 ', required=True, size=1,
                                default='e', help="insert substitute code. ")
    code_for_five = fields.Char(string='5 ', required=True, size=1,
                                default='f', help="insert substitute code. ")
    code_for_six = fields.Char(string='6 ', required=True, size=1,
                               default='g', help="insert substitute code. ")
    code_for_seven = fields.Char(string='7 ', required=True, size=1,
                                 default='h', help="insert substitute code. ")
    code_for_eight = fields.Char(string='8 ', required=True,  size=1,
                                 default='i', help="insert substitute code. ")
    code_for_nine = fields.Char(string='9 ', required=True, size=1,
                                default='j', help="insert substitute code. ")
    active_check = fields.Boolean(string="Active", default=False,
                                  help="Enable to make code active.")
    date_check = fields.Datetime(default=datetime.datetime.today(),
                                 string="Date", help="Specify the date.")

    @api.onchange('active_check')
    def onchange_active_check(self):
        """Function to work on changing active_check boolean field"""
        for i in self.search([]):
            if i.active_check == self.active_check and self.active_check:
                self.active_check = False
                raise UserError(_("Only one rule for code can be"
                                  " active at a time"))
