# -*- encoding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2009 Italian Community (http://www). 
#    All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'IMPORT CATALOGHI FORNITORI',
    'version': '0.1',
    'category': 'Localisation/Italy',
    'description': """Importazione Cataloghi Articoli da Fornitori, formati csv/txt per ogni campo articolo chiede un numero colonna del file da importare""",
    'author': 'C & G Software sas',
    'website': 'http://www.cgsoftware.it',
    "depends" : ['base','account','base_vat','product'],
    "update_xml" : ['partner.xml','partner_wizard.xml','security/ir.model.access.csv'],
    "active": False,
    "installable": True
}

