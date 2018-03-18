# -*- coding: utf-8 -*-
##############################################################################
#
#    POS Fiscal Printer module for Odoo
#    Copyright (C) 2017 Rosen Vladimirov
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
####
# 1. група "0" - брой(0);
# 2. група "1" - с кредитна карта(1);
# 3. група "2" - с чек(2);
# 4. група "3" - с дебитна карта(3).
####

from openerp import models, fields

_FISCAL_CODES = [
                ('0','Payment in cash;'),
                ('1','Payment with credit card;'),
                ('2','payment with check;'),
                ('3','Payment with debit card'),
                ]

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cash_pfiscal_codes = fields.Selection(
                _FISCAL_CODES,
                'Fiscal chash codes for fiscal printers', default='0')
