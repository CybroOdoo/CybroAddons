# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
def zkextendfmt(self):
    """Send the command that requests the device extended format data."""
    try:
        test = self.exttrynumber
    except:
        self.exttrynumber = 1
    data_hex = self.data_recv.hex()
    data_seq = [data_hex[4:6], data_hex[6:8]]
    if self.exttrynumber == 1:
        plus1 = 0
        plus2 = 0
    else:
        plus1 = -1
        plus2 = +1

    desc = ": +" + hex(int('99', 16) + plus1).lstrip('0x') + ", +" + hex(
        int('b1', 16) + plus2).lstrip("0x")
    self.data_seq1 = hex(int(data_seq[0], 16) + int('99', 16) + plus1).lstrip(
        "0x")
    self.data_seq2 = hex(int(data_seq[1], 16) + int('b1', 16) + plus2).lstrip(
        "0x")

    if len(self.data_seq1) >= 3:
        self.data_seq1 = self.data_seq1[-2:]

    if len(self.data_seq2) >= 3:
        self.data_seq2 = self.data_seq2[-2:]

    if len(self.data_seq1) <= 1:
        self.data_seq1 = "0" + self.data_seq1

    if len(self.data_seq2) <= 1:
        self.data_seq2 = "0" + self.data_seq2

    counter = hex(self.counter).lstrip("0x")
    if len(counter):
        counter = "0" + counter
    data = ("0b00" + self.data_seq1 + self.data_seq2 + self.id_com + counter +
            "007e457874656e64466d7400")
    self.zkclient.sendto(bytes.fromhex(data), self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
    except:
        if self.exttrynumber == 1:
            self.exttrynumber = 2
            tmp = zkextendfmt(self)
        if len(tmp) < 1:
            self.exttrynumber = 1

    self.id_com = self.data_recv.hex()[8:12]
    self.counter = self.counter + 1
    return self.data_recv[8:]
