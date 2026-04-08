# -- coding: utf-8 --
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    def create(self, vals):
        """Update records on adding new chair user"""
        # Handle both single record (dict) and multiple records (list) cases
        vals_list = vals if isinstance(vals, list) else [vals]

        # Set read_only_checker for all records
        for val in vals_list:
            val['read_only_checker'] = True

        # Create the records first
        records = super(SalonChairUser, self).create(vals)

        # Update user salon active status after creation
        all_active_users = []
        for chair in self.env['salon.chair'].search([]):
            if chair.user_id:
                all_active_users.append(chair.user_id.id)
                chair.user_id.write({'user_salon_active': True})
        for user in self.env['res.users'].search(
                [('id', 'not in', all_active_users)]):
            user.write({'user_salon_active': False})

        return records
