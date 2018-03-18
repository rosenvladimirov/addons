# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _, registry
from openerp.exceptions import except_orm, Warning, RedirectWarning

from openerp.report import interface

import csv
import os
import tempfile
import base64

import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


# http://jamesmcdonald.id.au/it-tips/using-gnubarcode-to-generate-a-gs1-128-barcode
# https://github.com/zint/zint

class report_xml(models.Model):
    _inherit = 'ir.actions.report.xml'

    ### Fields
    report_type = fields.Selection(selection_add=[('glabels', 'Glabels')])
    glabels_template = fields.Binary(string="Glabels template")
    csv_template = fields.Binary(string="CSV data template")
    label_count = fields.Integer(string="Count",default=1,help="One if you want to fill the sheet with new records, the count of labels of the sheet to fill each sheet with one record")

    @api.cr
    def _lookup_report(self, cr, name):
        if 'report.' + name in interface.report_int._reports:
            new_report = interface.report_int._reports['report.' + name]
        else:
            cr.execute("SELECT id, report_type,  \
                        model, glabels_template, csv_template, label_count  \
                        FROM ir_act_report_xml \
                        WHERE report_name=%s", (name,))
            record = cr.dictfetchone()
            if record['report_type'] == 'glabels':
                template = base64.b64decode(record['glabels_template']) if record['glabels_template'] else ''
                csv = base64.b64decode(record['csv_template']) if record['csv_template'] else ''
                new_report = glabels_report(cr, 'report.%s'%name, record['model'],template=template,csv=csv,count=record['label_count'])
            else:
                new_report = super(report_xml, self)._lookup_report(cr, name)
        return new_report


class glabels_report(object):

    def __init__(self, cr, name, model, template=None, csv=None, count=1 ):
        _logger.info("registering %s (%s)" % (name, model))
        self.active_prints = {}

        pool = registry(cr.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        name = name.startswith('report.') and name[7:] or name
        self.template = template
        self.csv = csv
        self.model = model
        self.count = count
        self.file = csv
        self.file_name = ''
        try:
            report_xml_ids = ir_obj.search(cr, 1, [('report_name', '=', name)])
            if report_xml_ids:
                report_xml = ir_obj.browse(cr, 1, report_xml_ids[0])
            else:
                report_xml = False
        except Exception, e:
            _logger.error("Error while registering report '%s' (%s)", name, model, exc_info=True)

    def create(self, cr, uid, ids, data, context=None):

        ctx = context.copy()
        magic_fields = {}
        temp = tempfile.NamedTemporaryFile(mode='w+t',suffix='.csv')
        outfile = tempfile.NamedTemporaryFile(mode='w+b',suffix='.pdf')
        glabels = tempfile.NamedTemporaryFile(mode='w+t',suffix='.glabels')
        glabels.write(base64.b64decode(data.get('template')) if data.get('template') else None or self.template)
        glabels.seek(0)

        pool = registry(cr.dbname)
        tax_obj = pool.get('account.tax')
        base_import_obj = pool.get('base_import.import')
        obj_precision = pool.get('decimal.precision')
        prec = obj_precision.precision_get(cr, uid, 'Account')
        currency_obj = pool.get('res.currency')
        user_obj = pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        base_url = pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')

        magic_fields.update({'creator': user.name})
        fields = self.file.replace('"','').replace('\n','').replace('\r','').split(',')
        fields = [v.decode('utf8') if isinstance(v, basestring) else v for v in fields]
        ctx['lang'] = user_obj.browse(cr,uid,uid).lang
        if user.company_id:
            magic_fields.update({'curr': user.company_id.currency_id.symbol})
        else:
            magic_fields.update({'curr': currency_obj.search(cr, uid, [('rate', '=', 1.0)])[1]})
        _logger.info("Glabels %s:%s:%s:%s:%s:%s:%s" % (cr, uid, ids, ctx, fields, magic_fields.items(), base_url))
        labelwriter = None
        for p in pool.get(self.model).read(cr,uid,ids,fields=None,context=ctx,load='_classic_read'):
            res = {}
            if not labelwriter:
                labelwriter = csv.DictWriter(temp, fields)
                labelwriter.writeheader()
            for k, v in p.items():
                _logger.info("Items %s:%s" % (k, v))
                # set print counter ++
                if isinstance(v, (int, float)):
                    if k == 'print_count':
                        pool.get(self.model).write(cr,uid,ids,{'print_count': v == 0 and 1 or v + 1},context=context)
                        continue
                if isinstance(v, tuple):
                    if k+'/id' in fields:
                        res.update({k+'/id':str(v[0])})
                    if k+'/id/name' in fields:
                        res.update({k+'/id/name':_(v[1])})
                elif isinstance(v, (str, unicode)):
                    if k in fields:
                        res.update({k:_(k == 'website_url' and "%s%s"% (base_url,v) or v)})
                elif isinstance(v, (int, float)):
                    if k+'/vat' in fields:
                        res.update({k+'/vat':str("{0:.2f}".format(round(tax_obj.browse(cr,uid,p['taxes_id']).compute_all(v, 1)['total_included'], prec)))})
                    if k in fields:
                        res.update({k:str(v)})
                else:
                    if k in fields:
                        res.update({k:v})
            for mk,mv in magic_fields.items():
                if mk in fields:
                    if isinstance(mv, (int, float)):
                        res.update({mk:str(mv)})
                    elif isinstance(mv, (str, unicode)):
                        res.update({mk:_(mv)})
            for c in range(self.count):
                labelwriter.writerow({k:isinstance(v, (str, unicode)) and v.encode('utf8') or v or '' for k,v in res.items()})
        temp.seek(0)
        #for row in csv.DictReader(temp):
        #    _logger.info("Lebel preforms %s" % row)
        res = os.system("glabels-3-batch -o %s -l -C -i %s %s" % (outfile.name,temp.name,glabels.name))
        outfile.seek(0)
        pdf = outfile.read()
        outfile.close()
        temp.close()
        glabels.close()
        return (pdf,'pdf')
