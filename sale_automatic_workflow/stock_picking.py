# -*- coding: utf-8 -*-
###############################################################################
#
#   sale_automatic_workflow for OpenERP
#   Copyright (C) 2011-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    workflow_process_id = fields.Many2one(comodel_name='sale.workflow.process',
                                          string='Sale Workflow Process')

#    @api.model
#    def write(self, vals):
#        _logger.info("Picking start %s" % vals)
#        if not vals.get('workflow_process_id') and vals.get('group_id'):
#            procurement = self.env['procurement.order'].search([('group_id', '=', vals.get('group_id'))], limit=1)
#            _logger.info("picking middle %s->%s" % (sale, procurement.workflow_process_id))
#            if procurement:
#                vals['workflow_process_id'] = procurement.workflow_process_id.id
#        _logger.info("Picking end %s" % vals)
#        return super(StockPicking, self).write(vals)

    def _create_invoice_from_picking(self, cr, uid, picking, vals,
                                     context=None):
        vals['workflow_process_id'] = picking.workflow_process_id.id
        if picking.workflow_process_id.invoice_date_is_order_date:
            vals['date_invoice'] = picking.sale_id.date_order

        _super = super(StockPicking, self)
        return _super._create_invoice_from_picking(cr, uid, picking, vals,
                                                   context=context)

    @api.multi
    def validate_picking(self):
        only_available = self.filtered(
            'workflow_process_id.ship_only_available')
        to_force = self - only_available
        if only_available:
            only_available.action_assign()
            only_available.do_prepare_partial()
            only_available.do_transfer()
        if to_force:
            to_force.force_assign()
            to_force.do_transfer()
        return True
