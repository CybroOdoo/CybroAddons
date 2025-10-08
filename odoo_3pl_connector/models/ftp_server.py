# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from ftplib import FTP
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FtpServer(models.Model):
    """Model to connect with FTP"""
    _name = 'ftp.server'
    _description = 'FTP Server'

    name = fields.Char(string='Name',
                       help='Name for FTP Server')
    host = fields.Char(string="Host",
                       help="Host of FTP server")
    username = fields.Char(string="Username",
                           help="Username of FTP server")
    password = fields.Char(string="Password",
                           help="Password of FTP server")

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited to create directories in FTP"""
        for vals in vals_list:
            try:
                ftp = FTP(vals['host'], vals['username'],
                          vals['password'])
                ftp.encoding = "utf-8"
                for item in ['Export_Sales', 'Export_Sales_Return',
                             'Export_Purchase', 'Import_Sales',
                             'Import_Sales_Return',
                             'Import_Purchase']:
                    ftp.mkd(item.replace(' ', '_'))
            except Exception as e:
                raise ValidationError(f"FTP Connection Error: {str(e)}")
        return super().create(vals_list)

    def unlink(self):
        """Inherited to removing directories from FTP"""
        for rec in self:
            try:
                ftp = FTP(rec.host,
                          rec.username,
                          rec.password)
                ftp.encoding = "utf-8"
                for item in ['Export_Sales', 'Export_Sales_Return',
                             'Export_Purchase', 'Import_Sales',
                             'Import_Sales_Return',
                             'Import_Purchase']:
                    ftp.rmd(item)
            except Exception as e:
                raise ValidationError(f"FTP Error: {str(e)}")
        return super().unlink()
