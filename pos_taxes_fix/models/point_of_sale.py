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

from openerp import models, api

class SaleOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_fix_taxes(self):
        user = self.env['res.users'].browse(self._uid)
        for order in self:
            # check order for fiscal positions for compatible and fix it
            if not order.fiscal_position:
                order.write({'fiscal_position': user.company_id.partner_id.property_account_position.id})
            # now check tax ids or get from product
            for line in order.lines:
                if not line.tax_ids:
                    line.write({'tax_ids': [(6, 0, [line.product_id.taxes_id.id])]})
