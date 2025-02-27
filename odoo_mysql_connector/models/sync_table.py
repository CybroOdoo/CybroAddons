# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class SyncTable(models.Model):
    """Model holding the sync details"""
    _name = 'sync.table'
    _description = 'Sync Table'

    mysql_field = fields.Char(string='Mysql Field',
                              help='Name of the field in Mysql database')
    data_type = fields.Char(string='Datatype',
                            help='Data type of the field in mysql')
    connection_id = fields.Many2one('mysql.connector', string='Connection',
                                    help='Connection corresponds to mapping')
    model_id = fields.Many2one(string='Model Name', help='Name of the model',
                               related='connection_id.model_id')
    ir_field_id = fields.Many2one('ir.model.fields', string='Odoo Field',
                                  help='Name of the field in Mysql database',
                                  domain="[('model_id', '=', model_id)]")
    ref_table = fields.Char(string='Reference Table',
                            help='Name of the reference table having '
                                 'foreign key')
    ref_col = fields.Char(string='Reference Column',
                          help='Id of the reference table having '
                               'foreign key')
    ref_col_name = fields.Char(string='Name of the Column in Reference Table',
                               help='Name of the column in reference table'
                                    ' to which the records to be compared')
    foreign_key = fields.Boolean(string='Foreign Key',
                                 help='True for for foreign keys')
    unique = fields.Char(string='Unique', help='Name of Unique field')
