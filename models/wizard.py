from odoo import models, fields, api, http
from datetime import date
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
# try:
#     from StringIO import StringIO
# except ImportError:
from io import BytesIO
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class wizard_reportes_chile(models.TransientModel):
    _name = 'wizard.reportes.chile'
    informe = fields.Selection([
        (1,'Cuenta Corriente por Empresa'),
        (2,'Libro de Ventas'),
        (3,'Libro de Compras'),
        (4,'Libro de Guias'),
        (5,'Libro de Honorarios'),
        (6,'Balance Tributario'),
        (7,'Libro Diario'),
        (8,'Libro Mayor'),
        ], 'Tipo de informe', required=True)
    arbol_id = fields.Many2one('account.account', domain="[('user_type.code','=','view')]")
    fecha_inicio = fields.Date('Fecha de inicio', default=date.today().replace(day=1))
    fecha_term = fields.Date('Fecha de termino',
        default=date.today().replace(day=1)+relativedelta(months=1, days=-1))
    partner_ids = fields.Many2many('res.partner')
    acount_ids = fields.Many2many('account.account')
    pendiente = fields.Boolean('Pendientes', default=True)
    file = fields.Binary(readonly=True)
    filename = fields.Char()
    #period_ids = fields.Many2many('account.period')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    section_id = fields.Many2one('crm.case.section')
    cabezera = fields.Boolean('Imprimir Cabezera', default=True)
    periodo_libro=fields.Many2one('wizard.periodo.libro',string="Periodo Libro",required=False, )


    @api.multi
    def _get_domain(self):
        search_domain=[]
        search_domain += [('company_id','=',self.company_id.id)]
        search_domain += [('date', '>=', self.fecha_inicio)]
        search_domain += [('date', '<=', self.fecha_term)]
        #search_domain += [('periodo_libro', '=', self.periodo_libro.name)]
        if self.partner_ids:
            search_domain+=[('partner_id', 'in', self.partner_ids.ids)]
        if self.section_id:
            search_domain += [('section_id','=', self.section_id.id)]
        return search_domain

    def _get_domain_libro_compra(self):
        search_domain=[]
        search_domain += [('company_id','=',self.company_id.id)]
        search_domain += [('periodo_libro', '>=', self.periodo_libro.id)]
        #search_domain += [('periodo_libro', '=', self.periodo_libro.name)]
        if self.partner_ids:
            search_domain+=[('partner_id', 'in', self.partner_ids.ids)]
        if self.section_id:
            search_domain += [('section_id','=', self.section_id.id)]
        return search_domain


    @api.multi
    def _get_domain_boletas(self):
        search_domain=[]
        search_domain += [('company_id','=',self.company_id.id)]
        search_domain += [('date_order', '>=', self.fecha_inicio)]
        search_domain += [('date_order', '<=', self.fecha_term)]
        #search_domain += [('periodo_libro', '=', self.periodo_libro.name)]
        if self.partner_ids:
            search_domain+=[('partner_id', 'in', self.partner_ids.ids)]
        if self.section_id:
            search_domain += [('section_id','=', self.section_id.id)]
        return search_domain


    @api.multi
    def imprimir_pdf(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.fecha_inicio,
                'date_end': self.fecha_term,
            },
        }

        if self.informe==1:
            report_name='l10n_cl_libros_contables.fact_abierta'
        elif self.informe==2:
            report_name='l10n_cl_libros_contables.libro_venta'
        elif self.informe==3:
            report_name='l10n_cl_libros_contables.libro_compra'
        elif self.informe==4:
            report_name='l10n_cl_libros_contables.libro_guias'
        elif self.informe==5:
            report_name='l10n_cl_libros_contables.libro_honorarios'
        elif self.informe==6:
            report_name='l10n_cl_libros_contables.balance_tributarios'
        elif self.informe==7:
            report_name='l10n_cl_libros_contables.libro_diarios'
        elif self.informe==8:
            report_name='l10n_cl_libros_contables.libro_mayors'
        try:
            informe = self.env.ref(report_name).report_action(self,config=False)

        except:
            #informe = self.env.ref(report_name).render_report(self)
            # informe = self.env['report'].get_action(self, report_name)
            informe = self.env.ref(report_name).report_action(self,config=False)
            #informe = {'type':'ir.actions.report', 'report_name':report_name}
        return informe

    @api.multi
    def imprimir_excel(self):
        #r = requests.get('http://localhost:8069/web/binary/download_document?informe=%s&wizard=%s'%(self.informe,int(self.id)), auth=HTTPBasicAuth('admin', 'opendrive1885'))
        #return r
        _logger.info(self)
        _logger.info(self.informe)
        _logger.info(self.id)
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/get_excel?informe=%s&wizard=%s'% (self.informe, self.id),
            'target': 'self'
        }
        # return {
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'wizard.reportes.chile.excel',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     'context': {'default_file':self.file, 'default_filename':self.filename}
        # }

    @api.multi
    def _excel_file(self,tabla,nombre):
        data2 = BytesIO()
        workbook = xlsxwriter.Workbook(data2, {'in_memory': True})
        datos = tabla
        worksheet2 = workbook.add_worksheet(nombre)
        worksheet2.set_column('A:Z', 20)
        columnas = list(datos.columns.values)
        columns2 = [{'header':r} for r in columnas]
        columns2[0].update({'total_string': 'Total'})
        currency_format = workbook.add_format({'num_format': '#,##0'})
        for record in columns2[1:]:
            record.update({'total_function': 'sum','format': currency_format})
        data = datos.values.tolist()
        col3 = len(columns2)-1
        col2=len(data)+1
        cells = xlsxwriter.utility.xl_range(0,0,col2,col3)
        worksheet2.add_table(cells, {'data': data, 'total_row': 1, 'columns':columns2})
        if nombre == 'Balance Tributario':
            row_format = workbook.add_format({
                'bg_color':'#4F81BD',
                'font_color':'white',
                'num_format': '#,##0',
                'bold': True
                })
            worksheet2.write_row(col2+1,0,
                ['Resultado del Ejercicio','',0,0,0,0,
                '=MAX(SUM(Table1[Pasivo])-SUM(Table1[Activo]),0)',
                '=MAX(-SUM(Table1[Pasivo])+SUM(Table1[Activo]),0)',
                '=MAX(SUM(Table1[Ganancia])-SUM(Table1[Perdida]),0)',
                '=MAX(-SUM(Table1[Ganancia])+SUM(Table1[Perdida]),0)'
                ],row_format)
            worksheet2.write_row(col2+2,0,
                ['TOTAL','',
                '=SUM(Table1[Debe])',
                '=SUM(Table1[Haber])',
                '=SUM(Table1[Deudor])',
                '=SUM(Table1[Acreedor])',
                '=SUM(Table1[Activo])+MAX(SUM(Table1[Pasivo])-SUM(Table1[Activo]),0)',
                '=SUM(Table1[Pasivo])+MAX(-SUM(Table1[Pasivo])+SUM(Table1[Activo]),0)',
                '=SUM(Table1[Perdida])+MAX(SUM(Table1[Ganancia])-SUM(Table1[Perdida]),0)',
                '=SUM(Table1[Ganancia])+MAX(-SUM(Table1[Ganancia])+SUM(Table1[Perdida]),0)'
                ],row_format)
        workbook.close()
        data2 = data2.getvalue()
        return data2

class wizard_reportes_chile_excel(models.TransientModel):
    _name = 'wizard.reportes.chile.excel'
    file = fields.Binary()
    filename = fields.Char()

class libro_ventas_tax_inherit(models.Model):
    _inherit = 'account.tax'
    mostrar_v = fields.Boolean('Mostrar en libro de venta')
    mostrar_c = fields.Boolean('Mostrar en libro de compra')


class PeriodoLibro(models.Model):
    _name = 'wizard.periodo.libro'
    _rec_name = 'name'
    _description = 'Periodos en facturas para la emisión del los libros de compra y venta'

    name = fields.Char(string="Periodo Libro")
    active = fields.Boolean(string="Activo?", default=True )

class Facturas(models.Model):
    _inherit = 'account.invoice'

    periodo_libro = fields.Many2one(comodel_name="wizard.periodo.libro", string="Periodo del Libro", required=False, )

class reportes_chile_controlador(http.Controller):

    @http.route('/web/get_excel', type='http', auth="user")
    @serialize_exception
    def download_document(self,informe,wizard,debug=0):
        informe = int(informe)
        filecontent = ''
        report_obj = request.env['wizard.reportes.chile']
        if informe==1:
            tabla = report_obj._facturas_abiertas(int(wizard))
            nombre = 'Informe Cuenta Corriente'
        if informe==2:
            tabla = report_obj._tabla_libro_venta(int(wizard))
            nombre = 'Libro de Ventas'
        if informe==3:
            tabla = report_obj._tabla_libro_compra(int(wizard))
            nombre = 'Libro de Compras'
        if informe==4:
            tabla = report_obj._libro_guias(int(wizard))
            nombre = 'Libro de Guias'
        if informe==5:
            tabla = report_obj._libro_honorarios(int(wizard))
            nombre = 'Libro de Honorarios'
        if informe==6:
            tabla = report_obj._balance_tributario(int(wizard))
            nombre = 'Balance Tributario'
        if informe==7:
            tabla = report_obj._libro_diario(int(wizard))
            nombre = 'Libro Diario'
        if informe==8:
            tabla = report_obj._libro_mayor_sql(int(wizard))
            nombre = 'Libro Mayor'
        if not tabla.empty and nombre:
            filecontent = report_obj._excel_file(tabla,nombre)
        if not filecontent:
            print("\nAAAAAAAAAAAAAA\n")
            return
            #return request.not_found()
        print("\nBBBBBBBBBBBBBBBBBBB\n")
        return request.make_response(filecontent,
        [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
        ('Content-Disposition', content_disposition(nombre+'.xlsx'))])
