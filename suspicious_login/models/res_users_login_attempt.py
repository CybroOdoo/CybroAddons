# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V  (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class ResUsersLoginAttempt(models.Model):
    """Model for user login attempts.This model records user login attempts,
     including details such as the user involved, login status
      (success or failure), reason for failure, location, IP address,
      login time, timezone, platform,and browser information."""
    _name = 'res.users.login.attempt'
    _description = 'User Login Attempt'

    user_id = fields.Many2one('res.users', string='User', help="Login User Id")
    status = fields.Selection([('failed', 'Failed'), ('success', 'Success')],
                              string='Status', help="Status of login attempt")
    failed_reason = fields.Char(string='Failed Reason',
                                help="Failed Reason of login attempt")
    location = fields.Char(string='Location',
                           help="Location of user when attempting the login")
    ip_address = fields.Char(string='IP Address', help="IP of user when login")
    login_time = fields.Datetime(string='Login Time', help="Login time of "
                                                           "user")
    timezone = fields.Char(string='TimeZone',
                           help="Timezone of user when attempting the login")
    platform = fields.Char(string='Platform',
                           help="Operating system of user when "
                                "attempting the login")
    browser = fields.Text(string='Browser',
                          help="Browser of user when attempting the login")
