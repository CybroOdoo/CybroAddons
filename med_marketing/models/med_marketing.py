from openerp import models, fields,api


class MedicalDepartments(models.Model):
    _name = 'pha_marketing.departments'

    name = fields.Char('Name of Department')


class MedicinesInfo(models.Model):
    _inherit = "product.template"

    uses_in = fields.Many2many('pha_marketing.departments', 'name')

