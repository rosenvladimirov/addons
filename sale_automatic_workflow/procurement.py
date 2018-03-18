# -*- encoding: utf-8 -*-
##############################################################################
#
#    Item number
#
#    Copyright (C) 2015 ICTSTUDIO (<http://www.ictstudio.eu>).
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

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class procurement_order(models.Model):
    _inherit = "procurement.order"

    workflow_process_id = fields.Many2one(comodel_name='sale.workflow.process',
                                          string='Automatic Workflow',
                                          ondelete='restrict')

    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        _logger.info("Procurement start %s" % vals)
        if not vals.get('workflow_process_id') and vals.get('sale_line_id'):
            order = self.env['sale.order.line'].search([('id', '=', vals.get('sale_line_id'))], limit=1)
            _logger.info("Procurement middle %s" % order)
            sale = self.env['sale.order'].search([('id', '=', order.order_id.id)])
            _logger.info("Procurement after middle %s->%s" % (sale, sale.workflow_process_id))
            if sale:
                vals['workflow_process_id'] = sale.workflow_process_id.id
        _logger.info("Procurement end %s" % vals)
        return super(procurement_order, self).create(vals)

#    def _run_move_create(self, cr, uid, procurement, context=None):
#        vals = super(procurement_order, self)._run_move_create(cr, uid, procurement, context=context)
#        _logger.info("Procurement move create order %s->%s" % (vals.get('workflow_process_id'), vals))
#        #group_id
#        if not vals.get('workflow_process_id'):
#            vals['workflow_process_id'] = self.pool.get('sale.order').browse(cr, uid, procurement.sale_line_id.order_id.id, context=context).workflow_process_id.id
#        _logger.info("Procurement move create order %s" % vals.get('workflow_process_id'))
#        return vals

#    def write(self, cr, uid, ids, vals, context=None):
#        _logger.info("Procurement start order %s" % (vals))
#        if vals.get('workflow_process_id'):
#            for proc in self.browse(cr, uid, ids, context=context):
#                if proc.sale_line_id and proc.sale_line_id.order_id:
#                    vals['workflow_process_id'] = self.pool.get('sale.order').browse(cr, uid, proc.sale_line_id.order_id.id, context=context).workflow_process_id.id
#                    stock_picking_ids = proc.sale_line_id.order_id.picking_ids
#                    if stock_picking_ids:
#                        stock_picking_ids = self.pool.get('stock.picking').write(cr, uid, [stock_picking_ids.id], {}, context=context)
#        _logger.info("Procurement end order %s:%s->%s" % (proc, vals, stock_picking_ids.id))
#        return super(procurement_order, self).write(cr, uid, ids, vals, context=context)
