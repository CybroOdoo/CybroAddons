# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class LawyerRecords(models.Model):
    _name = 'case.case'
    _description = 'Case Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    case_category = fields.Selection([('f', 'Family Cases'), ('c', 'Criminal Cases'), ('b', 'Traffic Cases'),
                                      ('j', 'Civil Cases')], string='Category of Case', required=True)
    case_details = fields.Text(string='Details Of Case (SECTION)', required=True)
    case_lawyer = fields.Many2one('hr.employee', string=" Lawyer", required=True, track_visibility='onchange')
    case_client = fields.Many2one('res.partner', string='Client', required=True, track_visibility='onchange',
                                  domain=[['customer', '=', 1]])
    case_court = fields.Many2one('court.court', string='Court', required=True)
    case_next = fields.Date(string='Sitting Date', required=True)
    case_menu = fields.One2many('case.case.line', 'connect_id', string="Sitting")
    case_note = fields.One2many('notes.notes', 'connect_id1', string="Internal Notes")
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    obj_attachment = fields.Integer(string='attachment', compute='attachments1')

    state = fields.Selection([('draft', 'Draft'),
                              ('invoiced', 'Invoiced'),
                              ('completed', 'Completed')], default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('case.case')
        return super(LawyerRecords, self).create(vals)

    @api.one
    def attachments1(self):
        obj_attachment = self.env['ir.attachment']
        for record in self:
            record.attachment_count = 0
        attachment_ids = obj_attachment.search([('res_model', '=', 'case.case'), ('res_id', '=', record.id)])
        if attachment_ids:
            record.obj_attachment = len(attachment_ids)

    @api.multi
    def count_attachments(self):
        self.ensure_one()
        domain = [('res_model', '=', 'case.case'), ('res_id', 'in', self.ids)]
        return {

            'name': 'ir.attachment tree',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context':  "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    @api.multi
    def make_payment(self):
        self.ensure_one()
        self.sudo().write({
            'state': 'invoiced'
        })

        ctx = {

            'default_corres_customer': self.case_client.id, 'default_employee_id': self.case_lawyer.id
        }
        return {
            'name': 'my.form',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': ctx,
        }

    @api.multi
    def add_sittings(self):
        self.ensure_one()
        self.sudo().write({
            'state': 'draft'
        })

    @api.multi
    def mark_done(self):
        self.ensure_one()
        self.sudo().write({
            'state': 'completed'
        })



class LawyerRecordsline(models.Model):
    _name = 'case.case.line'
    case_description = fields.Text(string='Description', required=True)
    connect_id = fields.Many2one('case.case', string='Description', required=True)
    case_date = fields.Date(string='Date', required=True)


class InternalNotes(models.Model):
    _name = 'notes.notes'
    case_internal = fields.Text(string='Internal Notes', required=True)
    connect_id1 = fields.Many2one('case.case', string='Internal Notes', required=True)


class Court(models.Model):
    _name = 'court.court'
    _rec_name = 'case_court'
    case_court = fields.Text(string='Court', required=True)


class PartnerForm(models.Model):

    _inherit = 'res.partner'

    class PartnerForm(models.Model):
        _inherit = 'res.partner'

        customer = fields.Boolean(string='Is a Client', default=True)


class Payslip(models.Model):

    _inherit = 'hr.payslip'

    corres_customer = fields.Many2one('res.partner',string='Customer')
