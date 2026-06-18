# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: K Sai Saran Varma (odoo@cybrosys.com)
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
################################################################################
import mysql.connector
from odoo import fields, models
from odoo.exceptions import ValidationError


class MysqlCredential(models.Model):
    """Model holding Mysql credentials"""
    _name = 'mysql.credential'
    _description = 'Mysql Credential'

    name = fields.Char(string='Database', help='Name of the database',
                       required=True)
    user = fields.Char(string='Username', help='Username of connection',
                       required=True)
    host = fields.Char(string='Host', help='Host name of MySQL connection',
                       required=True)
    password = fields.Char(string='Password',
                           help='Password of My SQL connection', required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('connect', 'Connected')],
                             string='State', help='State of the record',
                             readonly=True, default='draft')

    def action_connect(self):
        """Method for connecting with Mysql"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.name
            )
            if connection.is_connected():
                self.sudo().write({
                    'state': 'connect'
                })
        except mysql.connector.Error as e:
            # Handle any connection errors
            raise ValidationError(f"Error connecting to MySQL: {e}")
