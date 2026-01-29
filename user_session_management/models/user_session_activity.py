# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith PG (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class UserSessionActivity(models.Model):
    """
    Model to store the user session activities like record creation, 
    modification, deletion, and read.
    """
    _name = "user.session.activity"
    _description = "User Session Activity"

    name = fields.Char(string='Record Name', readonly=True,
                       help="Name of the record on which the activity occurred")
    user_id = fields.Many2one('res.users', string="User",
                              default=lambda s: s.env.user.id,
                              readonly=True, help="Session user")
    performed_date = fields.Datetime(string="Performed Date",
                                     default=fields.Datetime.now, readonly=True,
                                     help="Date on which the activity occurred")
    model = fields.Char(string="Model", readonly=True,
                        help="Model on which the activity occurred")
    record = fields.Integer(string='Record ID', readonly=True,
                            help="Record ID on which the activity occurred")
    records = fields.Char(string='Record IDs', readonly=True,
                          help="Record IDs on which the activity occurred")
    login_id = fields.Many2one('user.session.login', string='Session',
                               ondelete='restrict', readonly=True,
                               help="Session sequence on which the activity"
                                    "occurred")
    action = fields.Selection(selection=[('read', 'Read'),
                                         ('create', 'Create'),
                                         ('modify', 'Modify'),
                                         ('delete', 'Delete')],
                              readonly=True, string="Action",
                              help="Action performed on the record")
