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
from odoo import fields, models


class PipedriveRecord(models.Model):
    """Model to hold the Pipedrive Records"""
    _name = 'pipedrive.record'
    _description = 'Pipedrive Record'
    _rec_name = 'pipedrive_reference'

    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive reference of the record")
    record_type = fields.Selection(
        [('product', 'Product'), ('lead', 'Lead'), ('partner', 'Partner'), ('categ', 'Category')],
        string='Type',
        help='Type of record')
    odoo_ref = fields.Integer(string='Odoo Reference',
                              help="Odoo reference of the record")
