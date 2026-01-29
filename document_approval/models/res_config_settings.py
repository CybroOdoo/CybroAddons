# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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


class ResConfigSettings(models.TransientModel):
    """Inherit the model res.config.settings to add Additional fields"""
    _inherit = 'res.config.settings'

    visibility = fields.Selection(
        selection=[('all_user', 'All Users'), (
            'followers', 'Followers & Approvers'),
            ('approvers', 'Approvers')], string='Visibility',
        help='Restrict the visibility of the document', default="approvers",
        config_parameter='document_approval.visibility', required=True)

    @api.onchange('visibility')
    def _onchange_visibility(self):
        record_rule = self.env.ref('document_approval.'
                                   'document_approval_rule_user')
        if self.visibility == 'all_user':
            record_rule.write({
                'domain_force': "[(1, '=', 1)]",
            })
        elif self.visibility == 'followers':
            record_rule.write({
                'domain_force': "['|','|','|',('step_ids.approver_id.id','=',"
                                "user.id),('approve_initiator_id','=',"
                                "user.id),('team_id.team_lead_id.id','=',"
                                "user.id),('message_partner_ids', 'in', "
                                "[user.partner_id.id])]",
            })
        elif self.visibility == 'approvers':
            record_rule.write({
                'domain_force': "['|','|',('step_ids.approver_id.id','=',"
                                "user.id),('approve_initiator_id','=',user.id)"
                                ",('team_id.team_lead_id.id','=',user.id)]",
            })
