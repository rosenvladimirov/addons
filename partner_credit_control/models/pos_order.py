# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, _

class PosOrder(models.Model):
    _inherit = 'pos.order'

    credit_policy_id = fields.Many2one(
        'credit.control.policy',
        string='Credit Control Policy',
        help="The Credit Control Policy used for this "
             "invoice. If nothing is defined, it will "
             "use the account setting or the partner "
             "setting.",
        readonly=True,
        copy=False,
        groups="account_credit_control.group_account_credit_control_manager,"
               "account_credit_control.group_account_credit_control_user,"
               "account_credit_control.group_account_credit_control_info",
    )

    credit_control_line_ids = fields.One2many(
        'credit.control.line', 'pos_order_id',
        string='Credit Lines',
        readonly=True,
        copy=False,
    )

    @api.multi
    def action_cancel(self):
        """Prevent to cancel pos order related to credit line"""
        # We will search if this invoice is linked with credit
        cc_line_obj = self.env['credit.control.line']
        for pos_order in self:
            nondraft_domain = [('pos_order_id', '=', pos_order.id),
                               ('state', '!=', 'draft')]
            cc_nondraft_lines = cc_line_obj.search(nondraft_domain)
            if cc_nondraft_lines:
                raise api.Warning(
                    _('You cannot cancel this pos order.\n'
                      'A payment reminder has already been '
                      'sent to the customer.\n'
                      'You must create a credit note and '
                      'issue a new pos order.')
                )
            draft_domain = [('pos_order_id', '=', pos_order.id),
                            ('state', '=', 'draft')]
            cc_draft_line = cc_line_obj.search(draft_domain)
            cc_draft_line.unlink()
        return super(PosOrder, self).action_cancel()
