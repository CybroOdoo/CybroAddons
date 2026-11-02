# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import mysql.connector
from odoo import fields, models
from odoo.exceptions import ValidationError


class MysqlCredential(models.Model):
    """Model holding MySQL credentials and connection state."""
    _name = 'mysql.credential'
    _description = 'MySQL Credential'

    name = fields.Char(string='Database', help='Name of the database',
                       required=True)
    user = fields.Char(string='Username', help='Username of connection',
                       required=True)
    host = fields.Char(string='Host', help='Host name of MySQL connection',
                       required=True)
    password = fields.Char(help='Password of MySQL connection', required=True,
                           groups='base.group_system')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('connect', 'Connected')
    ], string='State', help='State of the record', readonly=True, default='draft')

    def action_connect(self):
        """Test and establish connection to the MySQL server."""
        self.ensure_one()
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.name
            )
            if connection.is_connected():
                self.write({'state': 'connect'})
        except mysql.connector.Error as e:
            raise ValidationError(
                self.env._("Error connecting to MySQL: %(error)s", error=e)
            )
        finally:
            if connection and connection.is_connected():
                connection.close()
