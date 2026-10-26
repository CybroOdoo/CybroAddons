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
from contextlib import contextmanager
from contextvars import ContextVar

from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import RedirectWarning, UserError

# Set only by the QA override wizard, inside the server. An Odoo context key
# would arrive with any RPC call and let a client skip the check.
_OVERRIDE = ContextVar('pharma_equipment_override', default=False)

OVERRIDE_FIELDS = (
    'pharma_equipment_override_by',
    'pharma_equipment_override_on',
    'pharma_equipment_override_reason',
)


@contextmanager
def equipment_override():
    """Allow recording a QA equipment override inside this block."""
    token = _OVERRIDE.set(True)
    try:
        yield
    finally:
        _OVERRIDE.reset(token)


class MrpProduction(models.Model):
    """Checks the equipment behind a manufacturing order on confirmation.

    The response is a site setting: no check, warn, or block. Where it
    blocks, QA can override with a written justification, which is posted to
    the order and raises a deviation where deviations are installed.
    """
    _inherit = 'mrp.production'

    pharma_equipment_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        relation='pharma_production_equipment_rel',
        column1='production_id',
        column2='equipment_id',
        string='Equipment Used',
        readonly=True,
        copy=False,
        help='GMP equipment behind the work centres of the order, recorded '
             'when it was confirmed.',
    )
    pharma_equipment_count = fields.Integer(
        string='Equipment',
        compute='_compute_pharma_equipment_count',
    )
    pharma_equipment_override_by = fields.Many2one(
        comodel_name='res.users', string='Equipment Override By',
        readonly=True, copy=False, tracking=True,
        help='QA reviewer who confirmed the order despite unfit equipment.')
    pharma_equipment_override_on = fields.Datetime(
        string='Equipment Override On', readonly=True, copy=False,
        help='When the equipment check was overridden.')
    pharma_equipment_override_reason = fields.Text(
        string='Override Justification', readonly=True, copy=False,
        help='Why QA allowed the order to proceed on unfit equipment.')

    def _compute_pharma_equipment_count(self):
        """Count the equipment recorded on the order."""
        for production in self:
            production.pharma_equipment_count = len(production.pharma_equipment_ids)

    def write(self, vals):
        """Only the QA override wizard records an override."""
        if any(name in vals for name in OVERRIDE_FIELDS) and not _OVERRIDE.get():
            raise UserError(self.env._('An equipment override is recorded through the '
                                       'Override Equipment Check wizard only.'))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Equipment resolution
    # ------------------------------------------------------------------
    def _pharma_resolve_workcenters(self):
        """Work centres of the order: its work orders, else its BoM operations.

        Empty for a BoM without operations.
        """
        self.ensure_one()
        workcenters = self.workorder_ids.workcenter_id
        if not workcenters and self.bom_id:
            workcenters = self.bom_id.operation_ids.workcenter_id
        return workcenters

    def _pharma_checked_equipment(self):
        """GMP-critical manufacturing equipment behind the order's work centres."""
        self.ensure_one()
        workcenters = self._pharma_resolve_workcenters()
        if not workcenters:
            return self.env['maintenance.equipment']
        Equipment = self.env['maintenance.equipment'].sudo()
        equipment = Equipment.search([('workcenter_ids', 'in', workcenters.ids)])
        # mrp_maintenance (Enterprise) links equipment to one work centre.
        if 'workcenter_id' in Equipment._fields:
            equipment |= Equipment.search([('workcenter_id', 'in', workcenters.ids)])
        return equipment

    def _pharma_is_sterile_product(self):
        """Whether the order makes a sterile product."""
        self.ensure_one()
        return bool(self.product_id.product_tmpl_id.sudo().pharma_sterile_product)

    def _pharma_equipment_issues(self):
        """Unfit equipment of the order: {equipment: [reasons]}."""
        self.ensure_one()
        equipment = self._pharma_checked_equipment()
        checked = equipment.filtered(
            lambda e: e.gmp_critical and e.equipment_class == 'manufacturing')
        checked._pharma_refresh_states()
        sterile = self._pharma_is_sterile_product()
        issues = {}
        for item in checked:
            reasons = item._pharma_fitness_issues(product=self.product_id, sterile=sterile)
            if reasons:
                issues[item] = reasons
        return issues

    @staticmethod
    def _pharma_issues_text(issues):
        """Plain-text list of the unfit equipment."""
        return '\n'.join('• %s: %s' % (item.display_name, ', '.join(reasons))
                         for item, reasons in issues.items())

    @staticmethod
    def _pharma_issues_html(issues):
        """HTML list of the unfit equipment, for the chatter."""
        return Markup('<ul>%s</ul>') % Markup('').join(
            Markup('<li><b>%s</b>: %s</li>') % (item.display_name, ', '.join(reasons))
            for item, reasons in issues.items())

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------
    def action_confirm(self):
        """Check the equipment before confirming, as the site setting says."""
        mode = self.env['maintenance.equipment']._pharma_equipment_settings()['check']
        warnings = {}
        if mode != 'off':
            for production in self.filtered(lambda p: p.state == 'draft'):
                issues = production._pharma_equipment_issues()
                if not issues:
                    continue
                if mode == 'block' and not production.pharma_equipment_override_on:
                    production._pharma_raise_unfit(issues)
                warnings[production] = issues
        res = super().action_confirm()
        for production in self:
            equipment = production._pharma_checked_equipment()
            if equipment:
                production.sudo().pharma_equipment_ids = [(6, 0, equipment.ids)]
        for production, issues in warnings.items():
            if production.pharma_equipment_override_on:
                continue
            production.message_post(body=Markup('<p>%s</p>') % self.env._(
                'Confirmed with unfit equipment (equipment check set to warn):'
            ) + self._pharma_issues_html(issues))
        if warnings and len(self) == 1 and not self.pharma_equipment_override_on:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'sticky': True,
                    'title': self.env._('Confirmed with unfit equipment'),
                    'message': self._pharma_issues_text(warnings[self]),
                    'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
                },
            }
        return res

    def _pharma_raise_unfit(self, issues):
        """Stop the confirmation; QA is offered the documented override."""
        self.ensure_one()
        message = self.env._(
            'Manufacturing order %(mo)s cannot be confirmed: equipment is not '
            'fit for use.\n\n%(issues)s',
            mo=self.name, issues=self._pharma_issues_text(issues))
        if self.env.user.has_group('pharmaceutical_base.group_pharma_qa_manager'):
            action = self.env.ref(
                'pharma_equipment_maintenance.pharma_equipment_override_wizard_action')
            raise RedirectWarning(
                message + '\n\n' + self.env._('As QA you may override the check with a '
                                              'written justification.'),
                action.id, self.env._('Override Equipment Check'),
                {'default_production_id': self.id, 'active_id': self.id})
        raise UserError(message + '\n\n' + self.env._(
            'Bring the equipment back into a fit state, or ask QA to override '
            'the check.'))

    def action_pharma_open_override(self):
        """Open the QA override wizard for this order."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pharma_equipment_maintenance.pharma_equipment_override_wizard_action')
        action['context'] = {'default_production_id': self.id}
        return action

    def _pharma_raise_override_deviation(self, issues, justification):
        """Raise a deviation for the override where deviations are installed."""
        self.ensure_one()
        if 'pharma.deviation' not in self.env:
            return False
        deviation = self.env['pharma.deviation'].sudo().create({
            'batch_id': self.id,
            'stage': 'manufacturing',
            'classification': 'major',
            'root_cause_category': 'equipment',
            'description': self.env._(
                'Manufacturing order %(mo)s was confirmed on equipment that '
                'was not fit for use, under a QA override.\n\n%(issues)s\n\n'
                'Justification: %(reason)s',
                mo=self.name, issues=self._pharma_issues_text(issues),
                reason=justification),
            'raised_by': self.env.user.id,
        })
        self.message_post(body=Markup('%s %s') % (
            self.env._('Deviation raised for the equipment override:'),
            deviation._get_html_link()))
        return deviation

    def button_mark_done(self):
        """A completed batch leaves its equipment dirty with this product."""
        res = super().button_mark_done()
        for production in self.filtered(lambda p: p.state == 'done'):
            equipment = production.pharma_equipment_ids or production._pharma_checked_equipment()
            equipment._pharma_register_use(production.product_id, production.date_finished)
        return res

    def action_view_pharma_equipment(self):
        """Equipment recorded on the order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Equipment Used'),
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.pharma_equipment_ids.ids)],
            'context': {'create': False},
        }
