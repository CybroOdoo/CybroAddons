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
from odoo import fields, models
from odoo.tools.translate import _


class PharmaIPQCResult(models.Model):
    """Adds the deviation link and auto-creates a deviation on IPQC failure."""
    _inherit = 'pharma.ipqc.result'

    deviation_id = fields.Many2one(
        comodel_name='pharma.deviation',
        string='Linked Deviation',
        copy=False,
        readonly=True,
        help='Deviation auto-created when this IPQC check fails.',
    )

    def _on_ipqc_fail(self):
        """Raise the deviation on IPQC failure if none is already linked."""
        for rec in self:
            if not rec.deviation_id:
                rec._auto_create_deviation()

    def _auto_create_deviation(self):
        """Auto-create a deviation when an IPQC result is marked Fail."""
        bmr = self.bmr_id
        dev = self.env['pharma.deviation'].create({
            'batch_id': bmr.production_id.id,
            'description': _(
                'IPQC Failure — Parameter: %(param)s\n'
                'Expected: %(expected)s\n'
                'Actual: %(actual)s\n'
                'Batch: %(batch)s',
                param=self.parameter,
                expected="%s - %s" % (self.expected_min, self.expected_max),
                actual=self.actual_value or '—',
                batch=bmr.batch_no,
            ),
            'immediate_action': _('IPQC check failed. Batch placed under investigation.'),
            'stage': 'manufacturing',
            'classification': 'major',
            'raised_by': self.env.user.id,
            'raised_on': fields.Datetime.now(),
        })
        # Bypass the write() override to avoid recursive re-entry
        super(PharmaIPQCResult, self).write({'deviation_id': dev.id})

        bmr.message_post(
            body=_(
                'IPQC FAIL on "%(param)s". Deviation %(dev)s auto-raised. '
                'Linked step placed on Hold.',
                param=self.parameter,
                dev=dev.name,
            )
        )
