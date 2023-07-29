# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: LAJINA.K.V (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class LegalCasePdfDocumentReport(models.AbstractModel):
    """Case registration report"""
    _name = 'report.legal_case_management.report_case_register_document'
    _description = "Report For Case Registration"

    def _get_report_values(self, docids, data=None):
        """Return the Report Values"""
        case_record = self.env['case.registration'].browse(docids)
        evidences = self.env['legal.evidence']. \
            search([('client_id', '=', case_record.client_id.id),
                    ('case_id', '=', case_record.id)])
        trials = self.env['legal.trial']. \
            search([('client_id', '=', case_record.client_id.id),
                    ('case_id', '=', case_record.id)])
        return {
            'case_record': case_record,
            'evidence': evidences,
            'trial': trials
        }
