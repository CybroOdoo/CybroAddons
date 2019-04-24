##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################

from odoo import models, fields


class ResPartnerPatient(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string='Is Patient')
    is_physician = fields.Boolean(string='Is Physician')
    speciality = fields.Many2one('physician.speciality', string='Speciality')
    hospital = fields.Many2one('res.partner', string='Hospital')


