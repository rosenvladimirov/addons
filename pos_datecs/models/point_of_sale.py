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

from openerp import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_fiscal_printer = fields.Boolean(
        'Fiscal Printer',
        help="A Fiscal printer is available on the Proxy")