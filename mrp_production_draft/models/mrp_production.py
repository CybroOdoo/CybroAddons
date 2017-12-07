# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError

from odoo.addons.mrp.models.mrp_production import MrpProduction as mp


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='draft', track_visibility='onchange')

    @api.model
    def create(self, values):
        production = super(mp, self).create(values)
        return production

    @api.multi
    def unlink(self):
        if any(production.state not in ['draft', 'cancel'] for production in self):
            raise UserError(_('Cannot delete a manufacturing order not in draft or cancel state'))
        return super(MrpProduction, self).unlink()

    @api.multi
    def action_confirm(self):
        if not self.name or self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
            print self.name
        if not self.procurement_group_id:
            self.procurement_group_id = self.env["procurement.group"].create({'name': self.name}).id
        self._generate_moves()
        self.state = 'confirmed'
