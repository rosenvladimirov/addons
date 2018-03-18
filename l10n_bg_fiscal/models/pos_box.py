# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, api, exceptions, fields, _
from openerp.addons.point_of_sale.wizard.pos_box import PosBox

from lxml import etree
import simplejson
import requests
_logger = logging.getLogger(__name__)

class PosBoxCashMoveReason(PosBox):
    _register = False

    @api.model
    def print_receipt(box, function):
        url = "http://%s:%s/hw_proxy/print_receipt"
        headers = {'Content-Type': 'application/json'}
        _logger.info("Object %s:%s" % (box._uid,box.env['pos.session'].browse(box._uid)))
        user = box.env['res.users'].browse(box._uid)
        session = box.env['pos.session'].search([('state','in',('opening_control','opened','closing_control')), ('user_id','=',user.id)], limit=1)

        pconf = box.env['pos.config'].browse(session.config_id.id)
        if pconf.iface_fprint_via_proxy:
            ip_port = pconf.proxy_ip.split(":")
            ip = ip_port[0]
            port = len(ip_port)>1 and int(ip_port[1]) or 8069
            url = url % (ip, port)
            product = box.env['product.template'].browse(box.product_id.id)
            taxes = box.env['account.tax'].browse(product.taxes_id.id)
            _logger.info("Product and taxes %s:%s:%s:%s:%s" % (pconf.chash_journal_id,url,product, taxes, taxes.id))
            receipt = {"params": {"printer":'fprint', "funct": function, "receipt": {
                        "orderlines": [{
                                        'price': box.amount,
                                        'price_display':  box.amount,
                                        'tax': [taxes.id],
                                        'price_with_tax': box.amount,
                                        'price_without_tax': product.taxes_id.compute_all(box.amount, 1, inverce=True)['total_included'],
                                        'product_type': product.type,
                                        'product_name': box.name,
                                        'income_pdt': product.income_pdt,
                                        'expense_pdt': product.expense_pdt,
                                        'quantity': 1,
                                        'discount': 0,
                                        'unit_name': product.uom_id.name,
                                        }],
                        "cashier_id": session.user_id.id,
                        "cashier_password": session.user_id.cashier_password,
                        "total_with_tax": box.amount,
                        "total_paid": box.amount,
                        "client_id": pconf.company_id.id,
                        "header": pconf.receipt_header,
                        "footer": pconf.receipt_footer,
                        "currency": {"name": session.currency_id.name, "rounding": 0.01, "symbol": session.currency_id.symbol, "decimals": 2},
                        "paymentlines": [{"amount": box.amount, "journal": [pconf.chash_journal_id.id]}],
                        "company": {"company_id": pconf.company_id.id, "name": pconf.company_id.name,},
                        "precision": {"money": 2, "price": 2, "quantity": 3},
                        "tax_details": [{"tax": {"tax_pfiscal_codes": taxes.tax_pfiscal_codes}}]
                        }}}
            _logger.info("url %s:%s:%s" % (url,headers,receipt))
            requests.post(url, headers=headers, json=receipt)

    @api.onchange('product_id')
    def onchange_reason(self):
        for record in self:
            if record.product_id.id:
                record.name = record.product_id.name

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(PosBoxCashMoveReason, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        doc = etree.XML(res['arch'])
        if self.env.context.get('active_model', '') != 'pos.session':
            for node in doc.xpath("//field[@name='product_id']"):
                modifiers = {'invisible': True, 'required': False}
                node.set('invisible', '1')
                node.set('required', '0')
                node.set('modifiers', simplejson.dumps(modifiers))
        else:
            for node in doc.xpath("//field[@name='name']"):
                node.set('string', _('Description'))
        res['arch'] = etree.tostring(doc)
        return res



class PosBoxIn(PosBoxCashMoveReason):
    _inherit = 'cash.box.in'

    product_id = fields.Many2one(
        comodel_name='product.template', string='Reason',
        domain="[('income_pdt', '=', True)]")

    @api.model
    def _compute_values_for_statement_line(self, box, record):
        values = super(PosBoxIn, self)._compute_values_for_statement_line(
            box, record)
        if self.env.context.get('active_model', '') == 'pos.session':
            if box.product_id.id:
                product = box.product_id
                account_id = product.property_account_income.id or\
                    product.categ_id.property_account_income_categ.id
                if account_id:
                    values['account_id'] = account_id
                else:
                    raise exceptions.Warning(_("""You have to define an
                    income account on the related product"""))
            PosBoxCashMoveReason.print_receipt(box,"validate_order")
        return values


class PosBoxOut(PosBoxCashMoveReason):
    _inherit = 'cash.box.out'

    product_id = fields.Many2one(
        comodel_name='product.template', string='Reason',
        domain="[('expense_pdt', '=', True)]")

    @api.model
    def _compute_values_for_statement_line(self, box, record):
        values = super(PosBoxOut, self)._compute_values_for_statement_line(
            box, record)
        if self.env.context.get('active_model', '') == 'pos.session':
            if box.product_id.id:
                product = box.product_id
                account_id = product.property_account_expense.id or\
                    product.categ_id.property_account_expense_categ.id
                if account_id:
                    values['account_id'] = account_id
                else:
                    raise exceptions.Warning(_("""You have to define an
                    expense account on the related product"""))
            PosBoxCashMoveReason.print_receipt(box,"validate_order")
        return values

class PosBoxReports(models.BaseModel):
    _register = False

    @api.model
    def print_report(box, function, model='zreport'):
        url = "http://%s:%s/hw_proxy/print_reports"
        headers = {'Content-Type': 'application/json'}
        user = box.env['res.users'].browse(box._uid)
        session = box.env['pos.session'].search([('state','in',('opening_control','opened','closing_control')), ('user_id','=',user.id)], limit=1)
        pconf = box.env['pos.config'].browse(session.config_id.id)

        _logger.info("Pconfig (%s:%s:%s" % (user, pconf.iface_fprint_via_proxy, session))
        if pconf.iface_fprint_via_proxy:
            ip_port = pconf.proxy_ip.split(":")
            ip = ip_port[0]
            port = len(ip_port)>1 and int(ip_port[1]) or 8069
            url = url % (ip, port)
            if model == 'zreport':
                report = {"params": {"reports":
                                        {"month": box.month,
                                         "year": box.year,
                                        }, 
                                    "printer": 'fprint', "funct": function}}
            elif model == 'creport':
                report = {"params": {"reports":
                                        {"month": box.month,
                                         "year": box.year,
                                         "date_start": box.date_start,
                                         "date_end": box.date_end,
                                         "mode": box.mode,
                                         "filename": box.file_name,
                                        },
                                    "printer": 'fprint', "funct": function}}
            _logger.info("url %s:%s:%s" % (url,headers,report))
            requests.post(url, headers=headers, json=report)

class PosBoxZReport(PosBoxReports):
    _name = 'cash.box.zreport'

    def _get_types(self):
        return [
            ('X', _('X Report')),
            ('Z', _('Z Report')),
            ('P', _('Period Short Report')),
            ('D', _('Period Detail Report')),
            ]

    type = fields.Selection(
                _get_types,
                'Consumption Calculation Method', default='Z')
    month =  fields.Char(
                string='Enter Month MM', size=2)
    year =  fields.Char(
                string='Enter Year YY', size=2)
    type_report = fields.Boolean(
                string="Type of report", default=True)

    @api.multi
    def print_daily(self):
        for box in self:
            if box.type == "X":
                PosBoxReports.print_report(box, "x-report")
            elif box.type == "Z":
                PosBoxReports.print_report(box, "z-report")
            elif box.type == "P" and box.month and box.month != "00" and box.year == "00":
                PosBoxReports.print_report(box, "m-report")
            elif box.type == "P" and box.year and box.month == "00" and box.year != "00":
                PosBoxReports.print_report(box, "y-report")
            elif box.type == "D" and box.month and box.month != "00" and box.year == "00":
                PosBoxReports.print_report(box, "dm-report")
            elif box.type == "D" and box.year and box.month == "00" and box.year != "00":
                PosBoxReports.print_report(box, "dy-report")

class PosBoxCReport(PosBoxReports):
    _name = 'cash.box.creport'

    def _get_models(self):
        return [
            ('A', _('All documents')),
            ('F', _('Fiscal receipts')),
            ('N', _('Non fiscal receipts')),
            ('R', _('Non fiscal receipts with reverce print')),
            ('S', _('Service receipts')),
            ('X', _('X Reports')),
            ('Z', _('Z Reports'))
            ]

    mode = fields.Selection(
                _get_models,
                'Consumption Calculation Method', default='Z')
    date_start = fields.Date(
                string='Start Date',
                help='Enter the begin date of report')
    date_end = fields.Date(
                string='End Date',
                help='Enter the end date of report')
    print_it = fields.Boolean(
                string="Is Print", default=True)
    file_name = fields.Char(
                string='Enter File name', size=255)

    @api.multi
    def print_ctrl(self):
        for box in self:
            if box.print_it:
                PosBoxReports.print_report(box, "ctrl-report-print")
            else:
                PosBoxReports.print_report(box, "ctrl-report-file")

