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
# 1. група "А" - за стоки и услуги, продажбите на които са освободени от облагане с данък, за стоки и услуги, продажбите на които се облагат с 0 % ДДС, както и за продажби, за които не се начислява ДДС;
# 2. група "Б" - за стоки и услуги, продажбите на които се облагат с 20 % данък върху добавената стойност;
# 3. група "В" - за продажби на течни горива чрез измервателни средства за разход на течни горива;
# 4. група "Г" - за стоки и услуги, продажбите на които се облагат с 9 % данък върху добавената стойност.
####

from openerp import models, fields

_FISCAL_CODES = [
                ('A','Group "A" for goods and services the sales of which are exempt from tax for goods and services the sales of which are subject to 0% VAT and for sales for which VAT is not charged;'),
                ('B','Group "B" for goods and services the sales of which are subject to 20% value added tax;'),
                ('C','Group "C" for the sale of liquid fuels by measuring means for the consumption of liquid fuels;'),
                ('D','Group "D" for goods and services the sales of which are subject to 9% value added tax.'),
                ]

class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_pfiscal_codes = fields.Selection(
                _FISCAL_CODES,
                'Fiscal codes for fiscal printers', default='B')
