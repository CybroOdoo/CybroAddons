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


class LegalCasePdfReport(models.AbstractModel):
    """Report of module"""
    _name = 'report.legal_case_management.report_legal_case_details'
    _description = "Report For Case Registration"

    def _get_report_values(self, docids, data=None):
        """Get data to the pdf"""
        query = """select case_reg.name as case_name,case_reg.start_date as start_date,
         case_reg.end_date as end_date, res_client.name as client,
        lawyer.name as lawyer, court.name as court,res_judge.name as judge,
         INITCAP(case_reg.payment_method) as payment_method, INITCAP(case_reg.state) as state from case_registration case_reg 
        LEFT JOIN res_partner res_client ON case_reg.client_id = res_client.id 
        LEFT JOIN res_partner res_judge 
        ON case_reg.judge_id= res_judge.id  LEFT JOIN
        hr_employee lawyer ON lawyer.id = case_reg.lawyer_id  LEFT JOIN
        legal_court court ON case_reg.court_id = court.id"""
        if data['lawyer_id'] and data['client_id'] and data['court_id'] \
                and data['judge_id'] and data['start_date'] and data['end_date'] \
                and data['payment_method'] and data['state']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                                    court.name ='%s' AND res_judge.name = '%s' AND 
                                     case_reg.start_date = '%s' AND 
                                     case_reg.end_date = '%s' AND 
                                     case_reg.payment_method = '%s'
                                    AND case_reg.state = '%s' """ \
                     % (data['lawyer_id'], data['client_id'], data['court_id'],
                        data['judge_id'], data['start_date'], data['end_date'],
                        data['payment_method'], data['state'])
        elif data['lawyer_id'] and data['client_id'] and data['court_id'] \
                and data['judge_id'] and data['start_date'] and \
                data['end_date'] and data['payment_method']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                         court.name ='%s' AND res_judge.name = '%s' AND 
                         case_reg.start_date = '%s' AND case_reg.end_date = '%s' 
                         AND case_reg.payment_method = '%s' """ \
                     % (data['lawyer_id'], data['client_id'], data['court_id'],
                        data['judge_id'], data['start_date'], data['end_date'],
                        data['payment_method'])
        elif data['lawyer_id'] and data['client_id'] and data['court_id'] \
                and data['judge_id'] and data['start_date'] and data['end_date']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                         court.name ='%s' AND res_judge.name = '%s' AND 
                         case_reg.start_date = '%s' AND 
                         case_reg.end_date = '%s' """ % (data['lawyer_id'],
                                                         data['client_id'],
                                                         data['court_id'],
                                                         data['judge_id'],
                                                         data['start_date'],
                                                         data['end_date'])
        elif data['lawyer_id'] and data['client_id'] and data['court_id'] \
                and data['judge_id'] and data['start_date']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                         court.name ='%s' AND res_judge.name = '%s' AND 
                         case_reg.start_date = '%s'""" % (data['lawyer_id'],
                                                          data['client_id'],
                                                          data['court_id'],
                                                          data['judge_id'],
                                                          data['start_date'])
        elif data['lawyer_id'] and data['client_id'] and data['court_id'] \
                and data['judge_id']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                         court.name ='%s' AND res_judge.name = '%s'""" \
                     % (data['lawyer_id'],
                        data['client_id'],
                        data['court_id'],
                        data['judge_id'])

        elif data['lawyer_id'] and data['client_id'] and data['court_id']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                        court.name ='%s'""" % (data['lawyer_id'],
                                               data['client_id'],
                                               data['court_id'])
        elif data['lawyer_id'] and data['client_id'] and data['judge_id']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                               res_judge.name ='%s'""" % (data['lawyer_id'],
                                                          data['client_id'],
                                                          data['judge_id'])

        elif data['lawyer_id'] and data['client_id'] and data['start_date']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                                     case_reg.start_date ='%s'""" \
                     % (data['lawyer_id'], data['client_id'],
                        data['start_date'])
        elif data['lawyer_id'] and data['client_id'] and data['end_date']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                                               case_reg.end_date ='%s'""" \
                     % (data['lawyer_id'], data['client_id'],
                        data['start_date'])
        elif data['lawyer_id'] and data['client_id'] and data['payment_method']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                            case_reg.payment_method ='%s'""" \
                     % (data['lawyer_id'], data['client_id'],
                        data['payment_method'])
        elif data['lawyer_id'] and data['client_id'] and data['state']:
            query += f""" WHERE lawyer.name = '%s' AND res_client.name='%s' AND
                                   case_reg.state ='%s'""" % (data['lawyer_id'],
                                                              data['client_id'],
                                                              data['state'])
        elif data['lawyer_id'] and data['client_id']:
            query += f""" WHERE lawyer.name ='%s' AND
                          res_client.name='%s'""" % (data['lawyer_id'],
                                                     data['client_id'])
        elif data['lawyer_id'] and data['judge_id']:
            query += f""" WHERE lawyer.name ='%s' AND
                          res_judge.name='%s'""" % (data['lawyer_id'],
                                                    data['judge_id'])

        elif data['lawyer_id'] and data['court_id']:
            query += f""" WHERE lawyer.name ='%s' AND
                                 court.name='%s'""" % (data['lawyer_id'],
                                                       data['court_id'])
        elif data['lawyer_id'] and data['start_date']:
            query += f""" WHERE lawyer.name ='%s' AND
                                 case_reg.start_date='%s'""" \
                     % (data['lawyer_id'], data['start_date'])
        elif data['lawyer_id'] and data['end_date']:
            query += f""" WHERE lawyer.name ='%s' AND
                                      case_reg.end_date='%s'""" \
                     % (data['lawyer_id'], data['end_date'])
        elif data['lawyer_id'] and data['payment_method']:
            query += f""" WHERE lawyer.name ='%s' AND
                                      case_reg.payment_method='%s'""" \
                     % (data['lawyer_id'], data['payment_method'])
        elif data['lawyer_id'] and data['state']:
            query += f""" WHERE lawyer.name ='%s' AND
                         case_reg.state='%s'""" % (data['lawyer_id'],
                                                   data['state'])
        elif data['client_id'] and data['judge_id']:
            query += f""" WHERE res_client.name ='%s' AND
                         res_judge.name='%s'""" % (data['client_id'],
                                                   data['judge_id'])
        elif data['client_id'] and data['court_id']:
            query += f""" WHERE res_client.name ='%s' AND
                         court.name='%s'""" % (data['client_id'],
                                               data['court_id'])
        elif data['client_id'] and data['start_date']:
            query += f""" WHERE  res_client.name ='%s' AND
                         case_reg.start_date='%s'""" % (data['client_id'],
                                                        data['start_date'])
        elif data['client_id'] and data['end_date']:
            query += f""" WHERE  res_client.name ='%s' AND
                         case_reg.end_date='%s'""" % (data['client_id'],
                                                      data['end_date'])
        elif data['client_id'] and data['payment_method']:
            query += f""" WHERE  res_client.name ='%s' AND
                         case_reg.payment_method='%s'""" \
                     % (data['client_id'], data['payment_method'])
        elif data['client_id'] and data['state']:
            query += f""" WHERE  res_client.name ='%s' AND
                         case_reg.state='%s'""" % (data['client_id'],
                                                   data['state'])
        elif data['judge_id'] and data['court_id']:
            query += f""" WHERE  res_judge.name ='%s' AND
                         court.name='%s'""" % (data['judge_id'],
                                               data['court_id'])
        elif data['judge_id'] and data['start_date']:
            query += f""" WHERE  res_judge.name ='%s' AND
                                case_reg.start_date='%s'""" \
                     % (data['judge_id'], data['start_date'])
        elif data['judge_id'] and data['end_date']:
            query += f""" WHERE  res_judge.name ='%s' AND
                                case_reg.end_date='%s'""" % (data['judge_id'],
                                                             data['end_date'])
        elif data['judge_id'] and data['payment_method']:
            query += f""" WHERE  res_judge.name ='%s' AND
                                case_reg.payment_method='%s'""" \
                     % (data['judge_id'], data['payment_method'])
        elif data['judge_id'] and data['state']:
            query += f""" WHERE  res_judge.name ='%s' AND
                            case_reg.state='%s'""" % (data['judge_id'],
                                                      data['state'])
        elif data['court_id'] and data['start_date']:
            query += f""" WHERE  court.name ='%s' AND
                                   case_reg.start_date='%s'""" \
                     % (data['court_id'], data['start_date'])
        elif data['court_id'] and data['end_date']:
            query += f""" WHERE  court.name ='%s' AND
                                          case_reg.end_date='%s'""" \
                     % (data['court_id'], data['end_date'])
        elif data['court_id'] and data['payment_method']:
            query += f""" WHERE  court.name ='%s' AND
                          case_reg.payment_method='%s'""" \
                     % (data['court_id'], data['payment_method'])
        elif data['court_id'] and data['state']:
            query += f""" WHERE court.name ='%s' AND
                                 case_reg.state='%s'""" % (data['court_id'],
                                                           data['state'])
        elif data['start_date'] and data['end_date']:
            query += f""" WHERE case_reg.start_date ='%s' AND
                                        case_reg.end_date='%s'""" \
                     % (data['start_date'], data['end_date'])
        elif data['start_date'] and data['payment_method']:
            query += f""" WHERE case_reg.start_date ='%s' AND
                                        case_reg.payment_method='%s'""" \
                     % (data['start_date'], data['payment_method'])
        elif data['start_date'] and data['state']:
            query += f""" WHERE case_reg.start_date ='%s' AND
                                        case_reg.state='%s'""" \
                     % (data['start_date'], data['state'])
        elif data['start_date'] and data['payment_method']:
            query += f""" WHERE case_reg.start_date ='%s' AND
                                        case_reg.payment_method='%s'""" \
                     % (data['start_date'], data['payment_method'])
        elif data['end_date'] and data['payment_method']:
            query += f""" WHERE case_reg.end_date ='%s' AND
                        case_reg.payment_method='%s'""" \
                     % (data['end_date'], data['payment_method'])
        elif data['end_date'] and data['state']:
            query += f""" WHERE case_reg.end_date ='%s' AND
                         case_reg.state='%s'""" % (data['end_date'],
                                                   data['state'])
        elif data['payment_method'] and data['state']:
            query += f""" WHERE case_reg.payment_method='%s' AND
                         case_reg.state='%s'""" % (data['payment_method'],
                                                   data['state'])
        elif data['lawyer_id']:
            query += f""" WHERE lawyer.name ='%s' """ \
                     % (data['lawyer_id'])

        elif data['client_id']:
            query += f""" WHERE res_client.name ='%s' """ \
                     % (data['client_id'])

        elif data['judge_id']:
            query += f""" WHERE res_judge.name ='%s' """ \
                     % (data['judge_id'])

        elif data['court_id']:
            query += f""" WHERE court.name ='%s' """ \
                     % (data['court_id'])
        elif data['start_date']:
            query += f""" WHERE case_reg.start_date ='%s' """ \
                     % (data['start_date'])
        elif data['end_date']:
            query += f""" WHERE case_reg.end_date ='%s' """ \
                     % (data['end_date'])
        elif data['payment_method']:
            query += f""" WHERE case_reg.payment_method ='%s' """ \
                     % (data['payment_method'])
        elif data['state']:
            query += f""" WHERE case_reg.state ='%s' """ \
                     % (data['state'])
        self.env.cr.execute(query)
        return {
            'data': data,
            'docs': self.env.cr.dictfetchall()
        }
