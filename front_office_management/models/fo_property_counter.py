# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
##############################################################################


from odoo import models, fields, api,_
from odoo.exceptions import UserError


class VisitDetails(models.Model):
    _name = 'fo.property.counter'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'employee'
    _description = 'Property Details'

    employee = fields.Many2one('hr.employee',  string="Employee", required=True)
    date = fields.Date(string="Date", required=True)
    visitor_belongings = fields.One2many('fo.belongings', 'belongings_id_fov_employee', string="Personal Belongings",
                                         copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prop_in', 'Taken In'),
        ('prop_out', 'Taken out'),
        ('cancel', 'Cancelled'),
    ], track_visibility='onchange', default='draft',
        help='If the employee taken the belongings to the company change state to ""Taken In""'
             'when he/she leave office change the state to ""Taken out""')

    @api.one
    def action_cancel(self):
        self.state = "cancel"

    @api.one
    def action_prop_in(self):
        count = 0
        number = 0
        for data in self.visitor_belongings:
            if not data.property_count:
                raise UserError(_('Please Add the Count.'))
            if data.permission == '1':
                count += 1
            number = data.number
        if number == count:
            raise UserError(_('No property can be taken in.'))
        else:
            self.state = 'prop_in'

    @api.multi
    def action_prop_out(self):
        self.state = "prop_out"





