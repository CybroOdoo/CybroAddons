# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PharmaCapa(models.Model):
    """Corrective and Preventive Action (CAPA)."""
    _name = 'pharma.capa'
    _description = 'Corrective and Preventive Action (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'name desc'
    name = fields.Char(
        string='CAPA Number',
        default='New',
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the CAPA Number for this record.',
    )

    deviation_id = fields.Many2one(
        comodel_name='pharma.deviation',
        string='Source Deviation',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='No standalone CAPAs — every CAPA must originate from a deviation.',
    )

    deviation_count = fields.Integer(help='Specifies the Deviation Count for this record.',
        string='Deviation Count',
        compute='_compute_deviation_count',
    )

    def _compute_deviation_count(self):
        """Executes the _compute_deviation_count operation."""
        for rec in self:
            rec.deviation_count = 1 if rec.deviation_id else 0

    def action_view_deviation(self):
        """Executes the action_view_deviation operation."""
        self.ensure_one()
        return {
            'name': 'Source Deviation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pharma.deviation',
            'res_id': self.deviation_id.id,
        }

    capa_type = fields.Selection(
        selection=[
            ('corrective', 'Corrective'),
            ('preventive', 'Preventive'),
        ],
        string='CAPA Type',
        required=True,
        default='corrective',
        tracking=True,
            help='Specifies the CAPA Type for this record.',
    )

    root_cause = fields.Text(
        string='Root Cause',
        help='Detailed root cause identified through 5-Why or Ishikawa analysis.',
    )

    action_plan = fields.Text(
        string='Action Plan',
        help='What will be done, by whom, and by when.',
    )

    effectiveness_check = fields.Text(
        string='Effectiveness Check',
        help='Evidence that the CAPA actually fixed the problem.',
    )
    assigned_to = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        required=True,
        tracking=True,
        help='Specifies the Assigned To for this record.',
    )

    due_date = fields.Date(
        string='Due Date',
        tracking=True,
        help='Specifies the Due Date for this record.',
    )
    status = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('verified', 'Verified'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='open',
        required=True,
        copy=False,
        tracking=True,
            help='Specifies the Status for this record.',
    )
    closed_by = fields.Many2one(
        comodel_name='res.users',
        string='Closed By',
        copy=False,
        readonly=True,
        tracking=True,
        help='QA Director who closed after verifying effectiveness.',
    )

    closed_on = fields.Datetime(
        string='Closed On',
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the Closed On for this record.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to auto-assign a sequential CAPA number."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('pharma.capa') or 'New'
                )
        return super().create(vals_list)

    def action_start(self):
        """Move the CAPA from Open to In Progress."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can start a CAPA.'),
        )
        for rec in self:
            if rec.status != 'open':
                raise UserError(_('Only Open CAPAs can be started.'))
            rec.status = 'in_progress'
            rec.message_post(body=_('CAPA started by %s.') % self.env.user.name)

    def action_verify(self):
        """Mark the CAPA Verified once effectiveness evidence is recorded."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can verify a CAPA.'),
        )
        for rec in self:
            if rec.status != 'in_progress':
                raise UserError(_('Only In Progress CAPAs can be verified.'))
            if not rec.effectiveness_check:
                raise UserError(_(
                    'Record the Effectiveness Check evidence before verifying CAPA %s.'
                ) % rec.name)
            rec.status = 'verified'
            rec.message_post(body=_('CAPA verified by %s.') % self.env.user.name)

    def action_close(self):
        """Close a verified CAPA; restricted to QA Director."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can close CAPAs.'),
        )
        for rec in self:
            if rec.status != 'verified':
                raise UserError(_(
                    'Only Verified CAPAs can be closed. '
                    'CAPA %s is currently "%s".'
                ) % (rec.name, rec.status))
            if not rec.root_cause:
                raise UserError(_(
                    'Document the Root Cause before closing CAPA %s.'
                ) % rec.name)
            if not rec.action_plan:
                raise UserError(_(
                    'Document the Action Plan before closing CAPA %s.'
                ) % rec.name)
            rec.write({
                'status': 'closed',
                'closed_by': self.env.user.id,
                'closed_on': fields.Datetime.now(),
            })
            rec.message_post(
                body=_('CAPA closed by QA Director %s.') % self.env.user.name
            )
