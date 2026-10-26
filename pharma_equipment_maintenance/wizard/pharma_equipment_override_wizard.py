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
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.mrp_production import equipment_override


class PharmaEquipmentOverrideWizard(models.TransientModel):
    """QA confirms a manufacturing order despite unfit equipment.

    A block with no override gets circumvented; an undocumented override is
    worse than no block. The justification goes to the order's chatter and
    a deviation is raised where deviations are installed.
    """
    _name = 'pharma.equipment.override.wizard'
    _description = 'Equipment Check Override'
    _inherit = ['pharma.workflow.mixin']

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    equipment_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        string='Unfit Equipment',
        compute='_compute_issues',
        readonly=True,
    )
    issues_text = fields.Text(
        string='Findings',
        compute='_compute_issues',
        readonly=True,
    )
    justification = fields.Text(
        required=True,
        help='Why the batch may proceed on this equipment. Recorded on the '
             'order and on the deviation.',
    )

    @api.depends('production_id')
    def _compute_issues(self):
        """List the equipment that fails the check now."""
        for wizard in self:
            issues = wizard.production_id._pharma_equipment_issues() \
                if wizard.production_id else {}
            wizard.equipment_ids = [(6, 0, [e.id for e in issues])]
            wizard.issues_text = wizard.production_id._pharma_issues_text(issues) \
                if issues else self.env._('All equipment is currently fit for use.')

    def action_confirm_override(self):
        """Record the override, raise the deviation and confirm the order."""
        self.ensure_one()
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_qa_manager',
            self.env._('Only QA can override the equipment check.'),
        )
        production = self.production_id
        if production.state != 'draft':
            raise UserError(self.env._('Only a draft manufacturing order can be confirmed.'))
        justification = (self.justification or '').strip()
        if len(justification) < 10:
            raise UserError(self.env._('Write a justification of at least a few words.'))
        issues = production._pharma_equipment_issues()
        if not issues:
            return production.action_confirm()
        with equipment_override():
            production.sudo().write({
                'pharma_equipment_override_by': self.env.user.id,
                'pharma_equipment_override_on': fields.Datetime.now(),
                'pharma_equipment_override_reason': justification,
            })
        production.message_post(body=Markup('<p><b>%s</b></p>%s<p>%s</p>') % (
            self.env._('Equipment check overridden by %s.', self.env.user.name),
            production._pharma_issues_html(issues),
            self.env._('Justification: %s', justification),
        ))
        for item in issues:
            item.sudo().message_post(body=self.env._(
                'Used for %(mo)s under a QA override by %(user)s: %(reasons)s.',
                mo=production.name, user=self.env.user.name,
                reasons=', '.join(issues[item])))
        production._pharma_raise_override_deviation(issues, justification)
        # The decision is QA's; confirming also creates the batch record,
        # which the QA role may not create itself.
        production.sudo().action_confirm()
        return {'type': 'ir.actions.act_window_close'}
