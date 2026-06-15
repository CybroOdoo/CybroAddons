# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from xml.etree import ElementTree as ET
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_nhs_board_member = fields.Boolean(
        string='NHS Board Member',
        default=False, 
        index=True,
        help="Master flag. Setting to True reveals the NHS Board Member notebook page on the partner form. Used in domain filters across all NHS views."
    )
    nhs_trust_id = fields.Many2one(
        'nhs.trust', 
        string='NHS Trust', 
        index=True,
        help="Trust this person sits on the board of. Required if is_nhs_board_member=True (enforced by view)."
    )
    nhs_board_role = fields.Selection([
        ('chair', 'Chair'),
        ('ceo', 'Chief Executive Officer (CEO)'),
        ('medical_director', 'Medical Director'),
        ('nursing_director', 'Director of Nursing'),
        ('finance_director', 'Director of Finance'),
        ('exec', 'Executive Director'),
        ('non_exec', 'Non-Executive Director'),
        ('other', 'Other Board Member'),
    ], 
        string='Board Role', 
        index=True,
        help="Selection: chair / vice_chair / ceo / medical_director / director_of_nursing / "
             "finance_director / coo / exec_director / ned / associate_ned / governor / other."
             " NED = Non-Executive Director (independent oversight role)."
    )
    is_voting_member = fields.Boolean(
        string='Voting Member', 
        default=True,
        help="True for full voting board members. Default: True. Set False for advisors, observers, associate directors."
    )
    term_start_date = fields.Date(
        string='Term Start Date',
        help="Start of current appointment term."
    )
    term_end_date = fields.Date(
        string='Term End Date',
        help="End of current appointment term. Used to compute is_term_active."
    )
    appointment_authority = fields.Char(
        string='Appointment Authority', 
        help="Body that appointed this member (e.g. 'NHS Improvement', 'Council of Governors', 'Secretary of State')."
    )
    is_term_active = fields.Boolean(
        string='Term Active',
        compute='_compute_is_term_active',
        store=True,
        index=True,
        help="True if today's date is within [term_start_date, term_end_date]."
    )
    can_edit_board_member = fields.Boolean(
        string='Can Edit Board Member',
        compute='_compute_can_edit_board_member',
        help="True if the current user is an NHS Trust Manager or Administrator."
    )

    def _compute_can_edit_board_member(self):
        is_manager = self.env.user.has_group(
            'odoo_nhs_trust_management.group_nhs_trust_manager'
        )
        for rec in self:
            rec.can_edit_board_member = is_manager

    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id, view_type, **options)
        if view_type == 'list':
            board_view = self.env.ref(
                'odoo_nhs_trust_management.view_nhs_board_member_list',
                raise_if_not_found=False,
            )
            if (board_view and view_id == board_view.id and
                    not self.env.user.has_group(
                        'odoo_nhs_trust_management.group_nhs_trust_manager')):
                node = ET.fromstring(result['arch'])
                node.set('create', '0')
                node.set('delete', '0')
                result['arch'] = ET.tostring(node, encoding='unicode')
        return result

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('odoo_nhs_trust_management.group_nhs_trust_manager'):
            for vals in vals_list:
                if vals.get('is_nhs_board_member'):
                    raise UserError(
                        'Only NHS Trust Managers and Administrators can create board member records.'
                    )
        return super().create(vals_list)

    def write(self, vals):
        board_fields = {
            'is_nhs_board_member', 'nhs_trust_id', 'nhs_board_role',
            'is_voting_member', 'term_start_date', 'term_end_date',
            'appointment_authority',
        }
        if board_fields & set(vals):
            nhs_records = self.filtered('is_nhs_board_member')
            becoming_member = vals.get('is_nhs_board_member')
            if (nhs_records or becoming_member) and not self.env.user.has_group(
                'odoo_nhs_trust_management.group_nhs_trust_manager'
            ):
                raise UserError(
                    'Only NHS Trust Managers and Administrators can modify board member records.'
                )
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('odoo_nhs_trust_management.group_nhs_trust_manager'):
            if self.filtered('is_nhs_board_member'):
                raise UserError(
                    'Only NHS Trust Managers and Administrators can delete board member records.'
                )
        return super().unlink()

    def action_open_nhs_trust(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'NHS Trust',
            'res_model': 'nhs.trust',
            'res_id': self.nhs_trust_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.constrains('nhs_trust_id', 'is_nhs_board_member')
    def _check_trust_state_for_board_member(self):
        for partner in self:
            if partner.is_nhs_board_member and partner.nhs_trust_id:
                if partner.nhs_trust_id.state in ('dissolved', 'suspended'):
                    raise ValidationError(
                        'Cannot assign a board member to "%s" because the trust is %s.'
                        % (partner.nhs_trust_id.name, partner.nhs_trust_id.state.capitalize())
                    )

    @api.depends('term_start_date', 'term_end_date', 'is_nhs_board_member')
    def _compute_is_term_active(self):
        today = fields.Date.context_today(self)
        for partner in self:
            if not partner.is_nhs_board_member:
                partner.is_term_active = False
                continue
            start = partner.term_start_date
            end = partner.term_end_date
            if start and end:
                partner.is_term_active = start <= today <= end
            elif start:
                partner.is_term_active = start <= today
            elif end:
                partner.is_term_active = today <= end
            else:
                partner.is_term_active = True
