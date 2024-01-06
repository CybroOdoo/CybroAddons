# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Renjith (odoo@cybrosys.com)
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
from odoo import models


class IrHttp(models.AbstractModel):
    """ Class to get the button state in a session """
    _inherit = 'ir.http'

    def session_info(self):
        """ Inheriting the ir.http model and super the session_info function
            to use the value in JS """
        info = super(IrHttp, self).session_info()
        info["button_state"] = True if self.env[
                                           'ir.config_parameter'].get_param(
            'bill_digitization.digitize_bill') == 'True' else False
        return info
