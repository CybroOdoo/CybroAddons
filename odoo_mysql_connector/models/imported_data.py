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


class ImportedData(models.Model):
    """Model tracking imported records and audit logs."""
    _name = 'imported.data'
    _description = 'Imported Data'
    _order = 'id desc'

    model_id = fields.Many2one('ir.model', string='Model',
                               help='Name of the target Odoo model')
    mysql_ref = fields.Char(string='MySQL Reference',
                            help='Identifier of the record in MySQL database')
    mysql_table = fields.Char(string='MySQL Table',
                              help='Name of the source table in MySQL database')
    log_note = fields.Text(string='Log Note',
                           help='Log note regarding the import execution')
    odoo_ref = fields.Integer(string='Odoo Reference',
                              help='Identifier of the synchronized record in Odoo database')
