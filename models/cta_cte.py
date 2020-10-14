from odoo import models, fields, api, exceptions
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import xlsxwriter
from io import StringIO
import base64
import pandas as pd
import numpy as np
import logging

_logger = logging.getLogger(__name__)


class cta_cte_reportes_chile(models.TransientModel):
    _inherit = 'wizard.reportes.chile'

    @api.multi
    def _get_domain_fa(self):
        search_domain=[]
        search_domain = [
        ('user_type_id.type','in', ['receivable','payable'])
        ]
        if self.acount_ids:
            search_domain.append(('account_id','in', self.acount_ids.ids))
        search_domain.append(('company_id','=',self.company_id.id))
        if self.partner_ids:
            search_domain.append(('partner_id', 'in', self.partner_ids.ids))
        #search_domain += [('date', '>', self.fecha_inicio)]
        #search_domain += [('date', '<', self.fecha_term)]
        if self.section_id:
            search_domain.append(('section_id','=', self.section_id.id))
        search_domain+=['|',('full_reconcile_id','=', False),('full_reconcile_id.create_date','>', self.fecha_term)]
        return search_domain

    @api.multi
    def _facturas_abiertas(self,wizard=False):
        if wizard:
            wiz = self.search([('id','=',wizard)])
        else:
            wiz = self
        search_domain = wiz._get_domain_fa()
        docs = wiz.env['account.move.line'].search(search_domain, order='date asc')
        dic = OrderedDict([
            ('Nombre',''),
            ('RUT',''),
            ('TELEFONO',''),
            ('DIRECCION',''),
            ('Fecha',''),
            ('Periodo',''),
            ('Referencia',''),
            #('Diario',''),
            ('Cuenta',''),
            ('Fecha Venc.',''),
            ('Fecha Conciliacion',''),
            ('Debito',''),
            ('Credito',''),
            ('Saldo',''),
            ])
        lista = []
        for i in docs:
            #if i.reconcile_id:
            #    if i.reconcile_id.create_date<fecha:
            #        pass
            dicti = OrderedDict()
            dicti.update(dic)
            dicti['Nombre']=i.partner_id.name
            dicti['RUT']=i.partner_id.document_number
            dicti['TELEFONO']=i.partner_id.phone or ''
            if i.partner_id.city_id.name:
                dicti['DIRECCION']=i.partner_id.street + str(i.partner_id.city_id.name) or ''
            else:
                dicti['DIRECCION'] = i.partner_id.street  or ''
            dicti['Fecha']=i.date
            dicti['Periodo']=i.date
            #dicti['Referencia']=(i.invoice_id.supplier_invoice_number or i.invoice_id.number or i.ref)
            dicti['Referencia'] = i.invoice_id.sii_document_number
            #dicti['Diario']=i.journal_id.name
            dicti['Cuenta']=i.account_id.name
            dicti['Fecha Venc.']=i.date_maturity
            if i.full_reconcile_id:
                dicti['Fecha Conciliacion']=i.full_reconcile_id.create_date
            dicti['Debito']=i.debit
            dicti['Credito']=i.credit
            dicti['Saldo']=i.debit-i.credit
            lista.append(dicti)
        tabla = pd.DataFrame(lista)
        return tabla

