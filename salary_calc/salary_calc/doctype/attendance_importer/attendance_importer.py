# Copyright (c) 2024, allen.xu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd


class AttendanceImporter(Document):
	def validate_attachment(self):
		if len(self.attachments) == 0:
			frappe.throw('请先上传excel附件')

	def on_submit(self):
		self.get_attachments()
		self.validate_attachment()
		self.make_attendance_log()


	
	
	def get_attachments(self):
		self.attachments = frappe.get_all('File',
			filters={
				'attached_to_doctype':'Attendance Importer',
				'attached_to_name':self.name,
				'file_type': ['in',['xls','xlsx']]
			})
		
	@frappe.whitelist()
	def make_attendance_log(self):
		
		self.get_attachments()
		self.validate_attachment()
		
		for attachment in self.attachments:
			file = frappe.get_doc('File', attachment.name)
			try:
				file_path = './' + frappe.local.site + file.file_url
				dfs = pd.read_excel(file_path, sheet_name=None)
				for sheet_name, df in dfs.items():
					columns = ['员工号','应出勤天数','出勤天数']
					if all(col in df.columns for col in columns):
						for index, row in df.iterrows():
							row_data = row[columns].to_dict()
							doc = frappe.new_doc('Attendance Log')
							
							doc.update({
								'employee': row_data.get('员工号'),
								'attendance_date': self.posting_date,
								'expected_attendance_days': row_data.get('应出勤天数'),
								'attendance_days': row_data.get('出勤天数'),
								'file':file.name,
								'sheet_name':sheet_name,
								'attendance_importer':self.name
							})
							try:
								doc.insert().submit()
							except Exception as e:
								frappe.log_error(e)

			except Exception as e:
				frappe.log_error(e)