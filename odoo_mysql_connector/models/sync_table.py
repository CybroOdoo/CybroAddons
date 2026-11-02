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
from odoo import fields, models


class SyncTable(models.Model):
    """Model holding field mapping and synchronization configurations."""
    _name = 'sync.table'
    _description = 'Sync Table'

    mysql_field = fields.Char(string='MySQL Field',
                              help='Name of the field in MySQL database')
    data_type = fields.Char(string='Datatype',
                            help='Data type of the field in MySQL')
    connection_id = fields.Many2one('mysql.connector', string='Connection',
                                    help='Connection corresponding to mapping')
    model_id = fields.Many2one('ir.model', string='Model Name', help='Name of the model',
                               related='connection_id.model_id')
    ir_field_id = fields.Many2one('ir.model.fields', string='Odoo Field',
                                  help='Target Odoo field to be mapped',
                                  domain="[('model_id', '=', model_id)]")
    ref_table = fields.Char(string='Reference Table',
                            help='Name of the reference table having foreign key')
    ref_col = fields.Char(string='Reference Column',
                          help='Column of the reference table having foreign key')
    foreign_key = fields.Boolean(string='Foreign Key',
                                 help='True for foreign keys')
