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
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NhsHealthBoard(models.Model):
    _name = 'nhs.health.board'
    _description = 'NHS Scotland Health Board'
    _order = 'name'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name', 
        required=True, 
        index=True, 
        tracking=True,
        help="Full statutory name (e.g. 'NHS Greater Glasgow and Clyde'). Tracked on chatter."
    )
    code = fields.Char(
        string='ODS Code', 
        required=True, 
        index=True,
        help="Official Scottish Government Health Board code. Format S08000xxx for territorial,"
             " SBxxxx for national. Used in PHS / ISD Scotland reporting datasets — keep aligned with national codes."
    )
    short_name = fields.Char(
        string='Short Name',
        help="Optional short name (e.g. 'NHS GGC' for Greater Glasgow and Clyde)."
    )
    region_id = fields.Many2one(
        'nhs.region',
        string='NHS Region',
        domain="[('health_system', '=', 'nhs_scotland')]",
        index=True,
        help="Optional grouping region (North/East/West Scotland). National boards may leave this empty."
    )
    board_type = fields.Selection([
        ('territorial', 'Territorial Health Board'),
        ('national', 'National Health Board'),
    ], 
        string='Board Type', 
        required=True, 
        default='territorial', 
        index=True,
        help="Selection: 'territorial' or 'national'. Default: 'territorial'. Territorial boards serve"
             " a geographic population. National boards serve specific functions"
             " (e.g. ambulance, public health, training) Scotland-wide."
    )
    population_served = fields.Integer(
        string='Population Served',
        help="Resident population the board is responsible for (territorial only)."
    )
    headquarters_address = fields.Text(
        string='Headquarters Address',
        help="Free-text HQ address."
    )
    website = fields.Char(
        string='Website',
        help="Public board website."
    )
    trust_ids = fields.One2many(
        'nhs.trust', 
        'health_board_id', 
        string='Associated Trusts',
        help="Trusts whose health_board_id points here. In Scotland the Health Board IS often the Trust — but the data model supports both for flexibility."
    )
    trust_count = fields.Integer(
        string='Trusts Count', 
        compute='_compute_trust_count',
        help="Count of linked trusts."
    )
    active = fields.Boolean(
        string='Active', 
        default=True,
        help="Archive flag."
    )


    _code_unique = models.Constraint(
        'unique(code)',
        'The Health Board ODS code must be unique!',
    )

    @api.constrains('region_id')
    def _check_region_system(self):
        for board in self:
            if board.region_id and board.region_id.health_system != 'nhs_scotland':
                raise ValidationError('An NHS Scotland Health Board must belong to an NHS Scotland Region!')

    @api.depends('trust_ids')
    def _compute_trust_count(self):
        for board in self:
            board.trust_count = len(board.trust_ids)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for board, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", board.name)
        if 'code' not in default:
            for board, vals in zip(self, vals_list):
                base_code = board.code or ''
                new_code = base_code
                count = 1
                while self.env['nhs.health.board'].search_count([('code', '=', new_code)]):
                    new_code = f"{base_code}_{count}"
                    count += 1
                vals['code'] = new_code
        return vals_list
