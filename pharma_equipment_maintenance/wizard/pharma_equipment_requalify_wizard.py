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
from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

REQUALIFIABLE_STATES = ('qualified', 'requalification_due', 'expired')


class PharmaEquipmentRequalifyWizard(models.TransientModel):
    """QA records a requalification of qualified equipment right away.

    Requalification is not only periodic: a move, a major repair or a change
    of use calls for it now, without waiting for the due date. IQ, OQ and PQ
    stay done; the qualification is renewed from the requalification date
    and the next one is scheduled.
    """
    _name = 'pharma.equipment.requalify.wizard'
    _description = 'Equipment Requalification'
    _inherit = ['pharma.workflow.mixin']

    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    previous_qualification_date = fields.Date(
        related='equipment_id.qualification_date', string='Qualified On')
    previous_requalification_date = fields.Date(
        related='equipment_id.requalification_date', string='Was Due On')
    requalified_on = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='Date the requalification was approved.',
    )
    next_requalification_date = fields.Date(
        string='Next Requalification',
        compute='_compute_next_requalification_date',
        store=True,
        readonly=False,
        help='Proposed with the same interval as the last qualification, '
             'one year when there was none.',
    )
    protocol_ref = fields.Char(
        string='Requalification Protocol',
        required=True,
        help='Reference of the approved requalification protocol and report.',
    )
    reason = fields.Text(
        required=True,
        help='Why the equipment is requalified now: periodic, relocation, '
             'major repair, change of use...',
    )

    @api.depends('requalified_on', 'equipment_id')
    def _compute_next_requalification_date(self):
        """Keep the interval the equipment was qualified for."""
        for wizard in self:
            equipment = wizard.equipment_id
            if not wizard.requalified_on:
                wizard.next_requalification_date = False
                continue
            interval = relativedelta(years=1)
            if (equipment.qualification_date and equipment.requalification_date
                    and equipment.requalification_date > equipment.qualification_date):
                interval = relativedelta(
                    days=(equipment.requalification_date - equipment.qualification_date).days)
            wizard.next_requalification_date = wizard.requalified_on + interval

    def action_requalify(self):
        """Renew the qualification and record it on the equipment."""
        self.ensure_one()
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can requalify equipment.'),
        )
        equipment = self.equipment_id.sudo()
        if equipment.qualification_state not in REQUALIFIABLE_STATES:
            raise UserError(self.env._(
                'Only qualified equipment can be requalified. Complete IQ, OQ '
                'and PQ and set the qualification date first.'))
        if self.requalified_on > fields.Date.context_today(self):
            raise UserError(self.env._('The requalification date cannot be in the future.'))
        if not self.next_requalification_date or self.next_requalification_date <= self.requalified_on:
            raise UserError(self.env._('The next requalification must fall after the requalification date.'))
        reason = (self.reason or '').strip()
        if len(reason) < 10:
            raise UserError(self.env._('Write a reason of at least a few words.'))
        previous = equipment.qualification_date
        equipment.write({
            'qualification_date': self.requalified_on,
            'requalification_date': self.next_requalification_date,
            'qualification_protocol_ref': self.protocol_ref,
        })
        equipment.activity_feedback(
            ['pharma_equipment_maintenance.mail_activity_requalification_due'])
        equipment._pharma_refresh_states()
        equipment.message_post(body=Markup('<p><b>%s</b></p><p>%s</p><p>%s</p>') % (
            self.env._('Requalified on %(date)s by %(user)s (protocol %(ref)s).',
                       date=self.requalified_on, user=self.env.user.name, ref=self.protocol_ref),
            self.env._('Previously qualified on %(prev)s. Next requalification due %(next)s.',
                       prev=previous, next=self.next_requalification_date),
            self.env._('Reason: %s', reason),
        ))
        return {'type': 'ir.actions.act_window_close'}
