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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class SalonChairUser(models.Model):
    """Model to store chair users """
    _name = 'salon.chair.user'
    _description = 'Salon Chair User'

    read_only_checker = fields.Boolean(string="Checker", default=False,
                                       help="To check readonly")
    user_id = fields.Many2one(comodel_name='res.users',
                              required=True, help="Users")
    start_date = fields.Datetime(
        default=fields.Datetime.now, required=True,
        help="Starting date")
    end_date = fields.Datetime(default=False, help="Ending date")
    salon_chair_id = fields.Many2one(
        'salon.chair', string="Chair", required=True,
        ondelete='cascade', index=True, copy=False, help="Select salon chairs")

    @api.model_create_multi
    def create(self, vals_list):
        """Update records on adding new chair user"""
        for vals in vals_list:
            vals['read_only_checker'] = True

        records = super(SalonChairUser, self).create(vals_list)

        # Update user salon active status after creation
        active_users = self.env['salon.chair'].search(
            [('user_id', '!=', False)]).user_id
        active_users.write({'user_salon_active': True})
        self.env['res.users'].search([
            ('id', 'not in', active_users.ids),
            ('user_salon_active', '=', True),
        ]).write({'user_salon_active': False})

        return records
