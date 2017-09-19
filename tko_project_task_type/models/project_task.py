# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    ThinkOpen Solutions Brasil
#    Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
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

from openerp import models, api, fields
from datetime import datetime
from  dateutil.relativedelta import relativedelta


class ProjectProject(models.Model):
    _inherit = 'project.project'

    task_type_ids_domain = fields.Many2many('task.type', 'task_type_project_rel_domain', 'project_id', 'task_type_id',
                                            string='Task Types', compute='_get_task_type_ids')

    @api.one
    @api.depends('parent_id')
    def _get_task_type_ids(self):
        if self.parent_id and self.parent_id.task_type_ids:
            self.task_type_ids_domain = [(6, 0, self.parent_id.task_type_ids.ids)]
        else:
            self.task_type_ids_domain = [(6, 0, self.env['task.type'].search([]).ids)]

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.task_type_ids = [(6, 0, self.parent_id.task_type_ids.ids)]


class task_type(models.Model):
    _name = 'task.type'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer('Color Index', size=1)
    task_id = fields.Many2one('project.task', string='Task')
    compute_expected_duration = fields.Boolean(u'Compute Expected Duration')
    expected_duration = fields.Integer(u'Expected Time', default=1, required=False)
    expected_duration_unit = fields.Selection([('d', 'Day'), ('w', 'Week'), ('m', 'Month'), ('y', 'Year')],
                                              default='d', required=False, string=u'Expected Time Unit')


class project_task(models.Model):
    _inherit = 'project.task'

    type_name = fields.Char(
        compute='_get_type_name',
        store=True,
        string='Name')
    task_type_id = fields.Many2one('task.type', string='Type')
    color = fields.Integer(compute='_get_color', string='Color', store=False)

    @api.multi
    def name_get(self):
        result = []
        for task in self:
            task_type = task.task_type_id and task.task_type_id.name or ''
            result.append(
                (task.id, "%s %s" %
                 ('[' + task_type + ']', task.name or ' ')))
        return result

    @api.depends('task_type_id.name')
    def _get_type_name(self):
        for record in self:
            if record.task_type_id:
                record.type_name = record.task_type_id.name

    @api.depends('task_type_id.color')
    def _get_color(self):
        for record in self:

            if record.task_type_id:
                record.color = record.task_type_id.color

    @api.onchange('task_type_id')
    def _change_task_type(self):
        result = {'value': {}}
        days = weeks = months = years = 0
        deadline = self.date_deadline
        if self.task_type_id and self.task_type_id.compute_expected_duration:
            if self.task_type_id.expected_duration and self.task_type_id.expected_duration_unit:
                if self.task_type_id.expected_duration_unit == 'd':
                    days = self.task_type_id.expected_duration
                if self.task_type_id.expected_duration_unit == 'w':
                    weeks = self.task_type_id.expected_duration
                if self.task_type_id.expected_duration_unit == 'm':
                    months = self.task_type_id.expected_duration
                if self.task_type_id.expected_duration_unit == 'y':
                    years = self.task_type_id.expected_duration
                deadline = datetime.today() + relativedelta(years=years, months=months, weeks=weeks, days=days)

            result['value'].update({
                'color': str(self.task_type_id.color)[-1],
                'type_name': self.task_type_id.name,
                'date_deadline': deadline
            })
        return result

    @api.onchange('project_id')
    def _onchange_project(self):
        self.task_type_id = False
        res = super(project_task, self)._onchange_project()
        task_type_ids = self.project_id and self.project_id.task_type_ids and self.project_id.task_type_ids.ids or []
        return {'domain': {'task_type_id': [('id', 'in', task_type_ids)]}}


class ProjectProject(models.Model):
    _inherit = 'project.project'

    task_type_ids = fields.Many2many('task.type', string="Task Type")
