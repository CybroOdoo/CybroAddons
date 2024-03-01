# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import models


class PosCalculator(models.TransientModel):
    """ Calculator in POS Screen """
    _name = 'pos.calculator'
    _description = 'POS Calculator'

    def calculations(self, data):
        """ Perform calculations on the given mathematical expression """
        while data.endswith((".", "+", "-", "/", "%", "*"), len(data) - 1,
                            len(data)):
            data = data[:-1]
        if data.find("%") == -1:
            return str(eval(data))
        else:
            vals = data.split('%')
            while len(vals) > 1:
                new_val = eval(vals[len(vals) - 2]) * eval(
                    vals[len(vals) - 1]) / 100
                vals.pop()
                vals.pop()
                vals.append(str(new_val))
            return vals[0]
