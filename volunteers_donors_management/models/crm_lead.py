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


class CrmLead(models.Model):
    """This class extends the 'crm.lead' model to add custom fields related
    to donor and volunteer information."""
    _inherit = "crm.lead"

    donor_type_id = fields.Many2one('donor.type', string='Donor Type',
                                    related='partner_id.donor_type_id',
                                    help='The type of donor associated with '
                                         'this lead',
                                    readonly=False)
    volunteer_type_id = fields.Many2one('volunteer.type',
                                        string='Volunteer Type',
                                        related='partner_id.volunteer_type_id',
                                        help='The type of volunteer '
                                             'associated with this lead',
                                        readonly=False)
    volunteer_skill_ids = fields.Many2many('volunteer.skill',
                                           string='Volunteer Skill',
                                           help='The skills possessed by the '
                                                'volunteer associated with '
                                                'this lead',
                                           related=
                                           'partner_id.volunteer_skill_ids',
                                           readonly=False)
