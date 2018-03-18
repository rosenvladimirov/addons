# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Author: Rosen Vladimirov vladimirov.rosen@gmail.com
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

import logging

from openerp import models, api
from openerp.tools import float_is_zero

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_re_validate(self):
        for tmp_order in self:
            _logger.info("Order %s" % tmp_order)
            if float_is_zero(tmp_order.amount_total - tmp_order.amount_paid, self.env['decimal.precision'].precision_get('Account')) and not (tmp_order.state in ['paid', 'done', 'invoiced']):
                tmp_order.action_paid()
                #if tmp_order.invoice_ids:
                #    tmp_order.signal_workflow('invoice')
