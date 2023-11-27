# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class MaintenanceTeam(models.Model):
    """Model that handles the maintenance team """
    _name = "maintenance.team"
    _description = "Maintenance Team"

    name = fields.Char(string='Maintenance Team',
                       help='Name of the maintenance team')
    user_id = fields.Many2one('res.users', string='Team Leader',
                              help="Leader of Team",
                              domain=lambda self: [
                                  ('groups_id', 'in', self.env.ref(
                                      'hotel_management_odoo.'
                                      'maintenance_team_group_'
                                      'leader').id)])
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="Members of the Team",
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'hotel_management_odoo.'
                                          'maintenance_'
                                          'team_group_user').id)])
