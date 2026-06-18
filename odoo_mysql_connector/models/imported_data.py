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
from odoo import fields, models


class ImportedData(models.Model):
    """Model holding imported data"""
    _name = 'imported.data'
    _description = 'Imported Data'

    model_id = fields.Many2one('ir.model', string='Model',
                               help='Name of the model')
    mysql_ref = fields.Char(string='Mysql Reference',
                            help='ID of the record in mysql database')
    mysql_table = fields.Char(string='Mysql Table',
                              help='Name of the table in mysql database')
    log_note = fields.Text(string='Log Note',
                           help='Log note regarding the importing')
    odoo_ref = fields.Integer(string='Odoo Reference',
                              help='ID of the record in Odoo database')
