# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class FeeCategory(models.Model):
    """For managing the categories for university fees"""
    _name = 'fee.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Categories of university fees"

    name = fields.Char('Name', required=True,
                       help='Create a fee category suitable for institution.'
                            ' Like Institutional, Hostel, Transportation, '
                            'Arts and Sports, etc')
    journal_id = fields.Many2one('account.journal',
                                 domain="[('is_fee', '=', 'True')]",
                                 required=True, string='Journal',
                                 help='Setting up of unique journal '
                                      'for each category help to distinguish '
                                      'account entries of each category ')
