# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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


class LabelHistory(models.Model):
    """Model for keeping track of label change history."""
    _name = 'label.history'
    _description = "History of label changes"

    user_id = fields.Many2one('res.users', string='Changed by',
                              help='User who made the label change')
    date = fields.Datetime(string='Changed On',
                           help='Date and time of label change')
    model = fields.Char(string='Model Name',
                        help='Name of the model associated with the '
                             'label change')
    old_label = fields.Char(string='Label Before Change',
                            help='Previous label value')
    new_label = fields.Char(string='Label After Change',
                            help='New label value after the change')
