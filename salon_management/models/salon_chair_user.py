# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class SalonChairUser(models.Model):
    """Model to store chair users """
    _name = 'salon.chair.user'
    _description = 'Salon Chair User'

    read_only_checker = fields.Boolean(string="Checker", default=False,
                                       help="To check readonly")
    user_id = fields.Many2one(comodel_name='res.users', string="User",
                              required=True, help="Users")
    start_date = fields.Datetime(
        string="Start Date", default=fields.Datetime.now, required=True,
        help="Staring date")
    end_date = fields.Datetime(string="End Date", default=False, help="Ending "
                                                                      "date")
    salon_chair_id = fields.Many2one(
        'salon.chair', string="Chair", required=True,
        ondelete='cascade', index=True, copy=False, help="Select salon chairs")

    @api.model
    def create(self, val):
        """Update records on adding new chair user"""
        all_active_users = []
        for chair in self.env['salon.chair'].search([]):
            if chair.user_id:
                all_active_users.append(chair.user_id.id)
                chair.user_id.write({'user_salon_active': True})
        for user in self.env['res.users'].search(
                [('id', 'not in', all_active_users)]):
            user.write({'user_salon_active': False})
        val['read_only_checker'] = True
        return super(SalonChairUser, self).create(val)
