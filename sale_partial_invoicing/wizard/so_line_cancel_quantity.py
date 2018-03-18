# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 Acsone SA/NV (http://www.acsone.eu)
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

from openerp import models, fields, api, exceptions, _, workflow
import openerp.addons.decimal_precision as dp


class SaleLineCancelQuantity(models.TransientModel):
    _name = 'sale.order.line_cancel_quantity'

    line_ids = fields.One2many('sale.order.line_cancel_quantity_line',
                               'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields):
        ctx = self.env.context.copy()
        so_ids = ctx.get('active_ids', [])
        so_line_obj = self.env['sale.order.line']
        lines = []
        for so_line in so_line_obj.browse(so_ids):
            max_quantity = so_line.product_uom_qty - so_line.invoiced_qty -\
                so_line.cancelled_qty
            lines.append({
                'so_line_id': so_line.id,
                'product_qty': max_quantity,
                'price_unit': so_line.price_unit,
            })
        defaults = super(SaleLineCancelQuantity, self).default_get(fields)
        defaults['line_ids'] = lines
        return defaults

    @api.multi
    def cancel_quantity(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.cancelled_qty > line.product_qty:
                raise exceptions.Warning(
                    _("""Quantity to cancel is greater
                    than available quantity"""))
            # To allow to add some quantity already cancelled
            if line.cancelled_qty < 0 and\
                    abs(line.cancelled_qty) > line.so_line_id.cancelled_qty:
                raise exceptions.Warning(
                    _("""Quantity to cancel is greater
                    than quantity already cancelled"""))
            line.so_line_id.cancelled_qty += line.cancelled_qty
            workflow.trg_write(self._uid, 'sale.order',
                               line.so_line_id.order_id.id, self._cr)


class SaleLineCancelQuantityLine(models.TransientModel):
    _name = 'sale.order.line_cancel_quantity_line'

    so_line_id = fields.Many2one('sale.order.line', 'Sale order line',
                                 readonly=True)
    product_qty = fields.Float(
        'Quantity', digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    price_unit = fields.Float(related='so_line_id.price_unit',
                              string='Unit Price', readonly=True)
    cancelled_qty = fields.Float(
        string='Quantity to cancel',
        digits=dp.get_precision('Product Unit of Measure'))
    wizard_id = fields.Many2one('sale.order.line_cancel_quantity',
                                'Wizard')
