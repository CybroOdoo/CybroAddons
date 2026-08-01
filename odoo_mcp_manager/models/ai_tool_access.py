# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
##############################################################################
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Operation keys mirrored by the boolean fields below. Used both for validation
# and by ai.tool to map a built-in tool name to the operation it performs.
OPERATIONS = ('read', 'create', 'update', 'delete', 'unlink')

# Seeded on first install/upgrade with read-only access. Only models that are
# actually installed in the database are added (optional apps are skipped).
_DEFAULT_READ_MODELS = [
    'res.partner', 'res.users', 'res.company', 'res.groups',
    'product.template', 'product.product',
    'sale.order', 'sale.order.line',
    'purchase.order',
    'account.move', 'account.move.line',
    'crm.lead',
    'project.project', 'project.task',
    'stock.picking',
    'hr.employee',
    'calendar.event',
    'mail.message',
]


class AiToolAccess(models.Model):
    """Allow-list controlling which models (and operations) the generic
    built-in AI tools may touch.

    Enforced by :meth:`ai.tool._check_model_access`. A model with no rule (or an
    inactive rule) is denied for every operation. Destructive operations default
    to off and must be enabled explicitly by an administrator.
    """

    _name = 'ai.tool.access'
    _description = 'AI Tool Model Access Rule'
    _order = 'model_name'
    _rec_name = 'model_name'

    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade',
        help='Odoo model the AI tools are allowed to operate on.',
    )
    model_name = fields.Char(
        related='model_id.model', string='Technical Name',
        store=True, index=True, readonly=True,
    )
    active = fields.Boolean(default=True)
    allow_read = fields.Boolean(string='Read / Search', default=True)
    allow_create = fields.Boolean(string='Create', default=False)
    allow_update = fields.Boolean(string='Update', default=False)
    allow_delete = fields.Boolean(string='Delete', default=False)
    allow_unlink = fields.Boolean(
        string='Unlink Relations', default=False,
        help='Allow removing many2many/many2one links via the unlink_record tool.',
    )

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)',
         'There is already an access rule for this model.'),
    ]

    @api.model
    def is_allowed(self, model_name: str, operation: str) -> bool:
        """Return True if *operation* is permitted on *model_name*.

        Reads the rule with elevated rights (callers are typically the
        public/bot user). An absent or inactive rule denies everything.
        """
        if operation not in OPERATIONS:
            return False
        rule = self.sudo().search(
            [('model_name', '=', model_name), ('active', '=', True)], limit=1
        )
        return bool(rule) and bool(rule['allow_%s' % operation])

    @api.model
    def _seed_default_rules(self) -> None:
        """Seed read-only rules for common installed models, once.

        Invoked from data/default_ai_tool_access.xml on install and upgrade;
        guarded by a system parameter so administrator edits are never
        overwritten on a later module update.
        """
        params = self.env['ir.config_parameter'].sudo()
        if params.get_param('mcp_gateway.allowlist_seeded'):
            return
        ir_model = self.env['ir.model']
        for model_name in _DEFAULT_READ_MODELS:
            if model_name not in self.env:
                continue
            if self.sudo().search_count([('model_id.model', '=', model_name)]):
                continue
            model_rec = ir_model.search([('model', '=', model_name)], limit=1)
            if model_rec:
                self.sudo().create({'model_id': model_rec.id, 'allow_read': True})
        params.set_param('mcp_gateway.allowlist_seeded', '1')
        _logger.info('AiToolAccess: seeded default read-only allow-list rules')
