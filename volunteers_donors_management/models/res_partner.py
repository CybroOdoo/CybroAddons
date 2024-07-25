# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.info)
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


class ResPartner(models.Model):
    """ This class extends the 'res.partner' model to add fields for storing
    information about volunteers and donors.
    """
    _inherit = "res.partner"

    is_volunteer = fields.Boolean(string='Is Volunteer', help='Check this box '
                                                              'if the partner '
                                                              'is a volunteer')
    is_donor = fields.Boolean(string='Is Donor', help='Check this box if the '
                                                      'partner is a donor')
    volunteer_type_id = fields.Many2one('volunteer.type',
                                        String='Volunteer Type',
                                        help='The type of volunteer '
                                             'associated with this partner')
    volunteer_skill_ids = fields.Many2many('volunteer.skill',
                                           String='Volunteer Skill',
                                           help='The skills of the volunteer '
                                                'associated with this partner')
    donor_type_id = fields.Many2one('donor.type', String='Donor Types',
                                    help='The type of donor associated with '
                                         'this partner')
