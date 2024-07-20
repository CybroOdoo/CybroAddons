# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (<https://www.cybrosys.com>)
#
#    you can modify it under the terms of the GNU LESSER
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
##############################################################################
from odoo import fields, models


class AutoCapture(models.Model):
    """ For storing the details of unauthorized access """
    _name = 'auto.capture'
    _description = 'Auto Capture'
    _rec_name = "date"

    email = fields.Char(string="Email", help="Mail ID of the user")
    image = fields.Binary(string="Image", help="Image Of unauthorized user")
    date = fields.Datetime(string="Date & Time", help="Date and Time of "
                                                      "unauthorized access")
