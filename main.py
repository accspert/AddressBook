from PyQt5 import QtSql
from PyQt5 import QtWidgets
from PyQt5.QtSql import QSqlQuery

from PyQt5 import uic
from PyQt5 import QtGui

import sys
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ErrorLogger import *
import traceback
import pickle
from card_reader import *
from keyvalidator import *
from crypto import *


def handle_error(error):
    '''Handles exceptions by logging their tracebacks and displaying a critical QMessageBox.'''
    ErrorLogger.WriteError(traceback.format_exc())
    QtWidgets.QMessageBox.critical(None, 'Exception raised', format(error))



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        try:
            uic.loadUi("mainwindow.ui", self)

            self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
            self.db.setDatabaseName('people.db')
            self.db.open()

            self.setup_model()
            self.setup_group_model()
            self.setup_phone_model()
            self.setup_email_model()

            self.tableView.selectRow(0)
            header = self.tableView.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.lineEditId.hide()
            self.label_2.hide()

        except Exception as e:
            try: self.db.close()
            except AttributeError: pass     # if db wasn't created yet, we can safely ignore it
            handle_error(e)

        self.frameGroup.hide()

        self.tableView.selectionModel().selectionChanged.connect(lambda: [self.mapp_address(), self.setup_phone_model(), self.setup_email_model()])

        self.pushButtonSaveAddress.clicked.connect(self.save_address)
        self.pushButtonClose.clicked.connect(lambda: self.close())
        self.pushButtonHideShowDetail.clicked.connect(self.hide_show_detail)
        self.pushButtonSaveGroup.clicked.connect(self.save_group)
        self.pushButtonHideShowGroup.clicked.connect(self.hide_show_group)
        self.pushButtonBack.clicked.connect(lambda: self.group_mapper.toPrevious())
        self.pushButtonForward.clicked.connect(lambda: self.group_mapper.toNext())

        self.pushButtonImportVcf.clicked.connect(self.import_vfc)
        self.pushButtonExportVcf.clicked.connect(self.export_vfc)

        # Add
        self.pushButtonAddNewAddress.clicked.connect(lambda: [self.clearAddressFields(), self.model.insertRow(0),
                                                              self.mapper.toFirst(), self.lineEditForename.setFocus(),
                                                              self.model.setData(self.tableView.model().index(0, self.group_index, QModelIndex()), self.comboBoxGroup.currentIndex() + 1),
                                                              self.model.submitAll()])
        self.pushButtonAddNewGroup.clicked.connect(lambda: [self.clearGroupFields(), self.group_model.insertRow(0),
                                                            self.group_mapper.toFirst()])

        self.pushButtonAddPhone.clicked.connect(self.add_phone)
        self.pushButtonAddEmail.clicked.connect(self.add_email)

        # Delete
        self.pushButtonDeleteGroup.clicked.connect(self.delete_group)
        self.pushButtonDelete.clicked.connect(self.delete_person)
        self.pushButtonDeleteEmail.clicked.connect(self.delete_email)
        self.pushButtonDeletePhone.clicked.connect(self.delete_phone)

        self.comboBoxGroupFilter.view().pressed.connect(self.filter_table)
        self.clearFilterButton.clicked.connect(self.clear_filter_table)

        self.lineEditFilterForename.textChanged.connect(lambda: self.filter_by_text(self.lineEditFilterForename.text(), self.lineEditFilterLastname.text()))
        self.lineEditFilterLastname.textChanged.connect(lambda: self.filter_by_text(self.lineEditFilterForename.text(), self.lineEditFilterLastname.text()))


    def closeEvent(self, event):
        try: self.db.close()
        except Exception as e: handle_error(e)
        event.accept()

##########################################################################@setup
    def setup_phone_model(self):
        try:
            if self.lineEditId.text():
                person_id = int(self.lineEditId.text())
                self.phone_model = QtSql.QSqlQueryModel()

                self.phone_model.setQuery(f"select phonenumber from PhoneQ where PersonId = '{person_id}'")
                self.listViewPhone.setModel(self.phone_model)
        except Exception as e: handle_error(e)


    def setup_email_model(self):
        try:
            if self.lineEditId.text():
                person_id = int(self.lineEditId.text())
                self.email_model = QtSql.QSqlQueryModel()
                self.email_model.setQuery(f"select email from EmailQ where PersonId = {person_id}")
                self.listViewEmail.setModel(self.email_model)
        except Exception as e: handle_error(e)


    def setup_group_model(self):
        try:
            self.group_model = QtSql.QSqlTableModel()
            self.group_model.setTable("Groups")
            self.group_model.select()
            self.group_model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)

            self.group_mapper = QDataWidgetMapper()
            self.group_mapper.setModel(self.group_model)
            self.group_mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

            self.group_mapper.addMapping(self.lineEditGroupId, 0)
            self.group_mapper.addMapping(self.lineEditGroupName, 1)
            self.group_mapper.toFirst()
        except Exception as e: handle_error(e)


    def setup_model(self):
        try:
            self.model = QtSql.QSqlRelationalTableModel()

            self.model.setTable("person")
            self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
            self.model.setJoinMode(1)   # LeftJoin

            self.group_index = self.model.fieldIndex("groupid")     # foreign key
            self.model.setRelation(self.group_index, QtSql.QSqlRelation("groups", "id", "groupname"))
            self.relModelGroup = self.model.relationModel(self.group_index)
            self.comboBoxGroup.setModel(self.relModelGroup)
            self.comboBoxGroup.setModelColumn(self.relModelGroup.fieldIndex("groupname"))

            self.model.select()

            self.comboBoxGroupFilter.setModel(self.relModelGroup)
            self.comboBoxGroupFilter.setModelColumn(self.relModelGroup.fieldIndex("groupname"))

            self.tableView.setModel(self.model)

            self.mapper = QDataWidgetMapper()
            self.mapper.setModel(self.model)

            self.mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))
            self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

            self.mapper.addMapping(self.lineEditId, 0)
            self.mapper.addMapping(self.lineEditForename, 1)
            self.mapper.addMapping(self.lineEditSurename, 2)
            self.mapper.addMapping(self.dateEditBirthday, 3)
            self.mapper.addMapping(self.lineEditStreet, 4)
            self.mapper.addMapping(self.lineEditZip, 5)
            self.mapper.addMapping(self.lineEditCity, 6)
            self.mapper.addMapping(self.lineEditCountry, 7)
            self.mapper.addMapping(self.comboBoxGroup, self.group_index)
            self.mapper.addMapping(self.plainTextEditMergedAddress, 9)

            self.mapper.toFirst()
        except Exception as e: handle_error(e)

####################################################################@hide_show
    def hide_show_group(self):
        if self.frameDetail.isVisible():
            self.frameDetail.hide()
        if self.frameGroup.isVisible():
            self.frameGroup.hide()
            self.pushButtonHideShowGroup.setText('Show Group')
        else:
            self.frameGroup.show()
            self.pushButtonHideShowGroup.setText('Hide Group')
            self.pushButtonHideShowDetail.setText('Show Detail')


    def hide_show_detail(self):
        if self.frameGroup.isVisible():
            self.frameGroup.hide()

        if self.frameDetail.isVisible():
            self.frameDetail.hide()
            self.pushButtonHideShowDetail.setText('Show Detail')
        else:
            self.frameDetail.show()
            self.pushButtonHideShowDetail.setText('Hide Detail')
            self.pushButtonHideShowGroup.setText('Show Group')

############################################################################@add
    def add_phone(self):
        try:
            if self.lineEditId.text():
                query = QSqlQuery()
                if self.lineEditAddPhone.text():
                    new_phone = self.lineEditAddPhone.text()
                    person_id = int(self.lineEditId.text())
                    query.exec("INSERT INTO phonenumbers (phonenumber)" f"VALUES ('{new_phone}')")

                    query.exec("SELECT max(PhoneNumberId) FROM Phonenumbers")
                    query.first()
                    phone_id = query.value(0)
                    query.exec("INSERT INTO person_phone_junction (PersonId, PhoneNumberId)" f"VALUES ('{person_id}', '{phone_id}')")
                    self.lineEditAddPhone.clear()
                    self.setup_phone_model()
            else:
                QtWidgets.QMessageBox.critical(None, 'Save a Person first', 'Save a Person first')
        except Exception as e: handle_error(e)


    def add_email(self):
        try:
            if self.lineEditId.text():
                query = QSqlQuery()
                if self.lineEditAddEmail.text():
                    new_email = self.lineEditAddEmail.text()
                    person_id = int(self.lineEditId.text())
                    query.exec("INSERT INTO emails (Email)" f"VALUES ('{new_email}')")

                    query.exec("SELECT max(EmailId) FROM emails")
                    query.first()
                    email_id = query.value(0)
                    query.exec("INSERT INTO person_email_junction (PersonId, EmailId)" f"VALUES ('{person_id}', '{email_id}')")
                    self.lineEditAddEmail.clear()
                    self.setup_email_model()
            else:
                QtWidgets.QMessageBox.critical(None, 'Save a Person first', 'Save a Person first')
        except Exception as e: handle_error(e)

#############################################################################@export
    def export_vfc(self):
        try:
            contacts = []
            contact_row = Contact()

            query_person = QSqlQuery()
            query_person_tel = QSqlQuery()
            query_person_email = QSqlQuery()

            query_person.exec("select * from person")
            while query_person.next():

                personId = query_person.value(0)
                contact_row.FirstName = query_person.value(1)
                contact_row.LastName = query_person.value(2)
                contact_row.Birthday = query_person.value(3)
                contact_row.Address = query_person.value(self.group_index)

                query_person_tel.exec(f"Select * from PhoneQ where PersonId = {personId}")
                while query_person_tel.next():
                    contact_row.Phonenumbers.append(query_person_tel.value(2))

                query_person_email.exec(f"Select * from EmailQ where PersonId = {personId}")
                while query_person_email.next():
                    contact_row.Email.append(query_person_email.value(2))


                contacts.append(contact_row)
                contact_row = Contact()

            vcards = create_vcards(contacts)

            fileName = QtWidgets.QFileDialog.getSaveFileName(self,
                    "Save Address Book", '',
                    "Address Book (*.vcf);;All Files (*)")
            fileName = fileName[0]
            filehandler = open(f"{fileName}", "wb")
            pickle.dump(vcards, filehandler, protocol=None)
            filehandler.close()

            file = open(fileName, 'rb')
            object_file = pickle.load(file)
            file.close()
        except Exception as e: handle_error(e)

#############################################################################@import
    def import_vfc(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(QtWidgets.QWidget(), 'Open a file', '',
                                                      'VCF Files (*.vcf)')
        if fname[0] != '':
            try:
                contacts = import_contacts(fname[0])
                query = QSqlQuery()
                temp_phone_list = []
                temp_email_list = []
    
                for contact in contacts:
                    query.exec("INSERT INTO person (forename, lastname, mergedAddress)"
                               f"VALUES ('{contact.FirstName}', '{contact.LastName}', '{contact.Address}' )")
                    query.exec("SELECT max(PersonId) FROM person")
                    query.first()
                    contact_id = query.value(0)
                    for number in contact.Phonenumbers:
                        temp_phone_list.append(number)
    
                    phone_list = list(set(temp_phone_list))     # remove duplicates
                    for number in phone_list:
                        query.exec("INSERT INTO phonenumbers (phonenumber)" f"VALUES ('{number}')")
                        query.exec("SELECT max(PhoneNumberId) FROM Phonenumbers")
                        query.first()
                        phone_id = query.value(0)
                        query.exec("INSERT INTO person_phone_junction (personid, phonenumberid) " f"VALUES ('{contact_id}', '{phone_id}')")
                    temp_phone_list.clear()
                    phone_list.clear()
    
                    for email in contact.Email:
                        temp_email_list.append(email)
    
                    email_list = list(set(temp_email_list))     # remove duplicates
                    for email in email_list:
                        query.exec("INSERT INTO Emails (email)" f"VALUES ('{email}')")
                        query.exec("SELECT max(EmailId) FROM Emails")
                        query.first()
                        email_id = query.value(0)
                        query.exec("INSERT INTO person_email_junction (personid, emailid) " f"VALUES ('{contact_id}', '{email_id}')")
    
                    temp_email_list.clear()
                    email_list.clear()
    
                    if contact.Birthday:
                        birthday = contact.Birthday
                        query.exec(f"Update Person set Birthday= '{birthday}' where PersonId= {contact_id} ")
    
                self.setup_model()
                self.setup_phone_model()
                self.setup_email_model()
                self.tableView.selectRow(0)
            except Exception as e:
                handle_error(e)
                return

##############################################################@save
    def save_group(self):
        try:
            if not self.lineEditGroupId.text():
                group_name = self.lineEditGroupName.text()
                query = QSqlQuery()
                query.exec("INSERT INTO Groups (GroupName)" f"VALUES ('{group_name}')")
                self.setup_group_model()
                self.setup_model()
        except Exception as e: handle_error(e)


    def save_address(self):
        self.tableView.selectRow(0)
        self.statusBar().showMessage('Person saved', 5000)

###########################################################@mapp
    def mapp_address(self):
        self.mapper.setCurrentModelIndex(self.tableView.currentIndex())

##########################################################@filter
    def filter_table(self, index):
        text = self.comboBoxGroupFilter.model().data(index)
        self.model.setFilter(f"groupname == '{text}'")
        self.tableView.setModel(self.model)
        self.clearAddressFields()
        self.model.select()


    def filter_by_text(self, text_forename, text_lastname):
        self.model.setFilter(f"forename like '{text_forename}%' and lastname like '{text_lastname}%'")
        self.tableView.setModel(self.model)
        self.clearAddressFields()
        self.model.select()

###########################################################@clear
    def clearGroupFields(self):
        try:
            self.lineEditGroupId.clear()
            self.lineEditGroupName.clear()
        except Exception as e: handle_error(e)


    def clearAddressFields(self):
        try:
            self.lineEditId.clear()
            self.lineEditForename.clear()
            self.lineEditSurename.clear()
            self.dateEditBirthday.setDate(QDate.currentDate())
            self.lineEditStreet.clear()
            self.lineEditZip.clear()
            self.lineEditCity.clear()
            self.lineEditCountry.clear()
            self.phone_model.clear()
            self.email_model.clear()
            self.lineEditAddEmail.clear()
            self.lineEditAddPhone.clear()
        except Exception as e: handle_error(e)


    def clear_filter_table(self):
        try:
            self.model.setFilter("")
            self.tableView.setModel(self.model)
            self.model.select()
            self.lineEditFilterForename.clear()
            self.lineEditFilterLastname.clear()
        except Exception as e: handle_error(e)

##############################################################@delete
    def delete_group(self):
        try:
            group_id = int(self.lineEditGroupId.text())
            query = QSqlQuery()
            query.exec(f"delete from Groups where id = '{group_id}'")
            self.clearGroupFields()
            self.setup_group_model()
        except Exception as e: handle_error(e)


    def delete_person(self):
        try:
            query_ppj = QSqlQuery()     # person_phone_junction
            query_p = QSqlQuery()       # phonenumbers
            query_pej = QSqlQuery()     # person_email_junction
            query_e = QSqlQuery()       # emails
            indexes = []

            rows = self.tableView.selectionModel().selectedRows()

            for row in rows:
                indexes.append(row.row())

                person_id = self.model.data(row, Qt.DisplayRole)
                query_ppj.exec(f"SELECT PhoneNumberId FROM PhoneQ where PersonId = {person_id}")
                while (query_ppj.next()):
                    phone_id = query_ppj.value(0)
                    query_p.exec(f"delete from Phonenumbers where PhoneNumberId = {phone_id}")

                query_ppj.clear()
                query_p.clear()

                query_ppj.exec(f"delete from person_phone_junction where PersonId = {person_id}")

            person_id = ''

            for row in rows:
                person_id = self.model.data(row, Qt.DisplayRole)
                query_pej.exec(f"SELECT EmailId FROM EmailQ where PersonId = {person_id}")
                while (query_pej.next()):
                    email_id = query_pej.value(0)
                    query_p.exec(f"delete from emails where EmailId = {email_id}")

                query_pej.clear()
                query_e.clear()

                query_pej.exec(f"delete from person_email_junction where PersonId = {person_id}")

            # Reverse sort rows indexes
            indexes = sorted(indexes, reverse=True)

            # Delete rows
            for rowidx in indexes:
                self.model.removeRow(rowidx)
                self.model.submitAll()
            self.model.select()
            self.clearAddressFields()
            self.tableView.selectRow(0)
        except Exception as e: handle_error(e)


    def delete_phone(self):
        try:
            person_id = self.lineEditId.text()
            query = QSqlQuery()
            if len(self.listViewPhone.selectedIndexes()) >= 1:
                for items in (self.listViewPhone.selectedIndexes()):
                    phone_number = (self.phone_model.record(items.row()).field(0).value())

                    query.exec(f"SELECT PhoneNumberId FROM PhoneQ  where PersonId =  {person_id} and PhoneNumber = '{phone_number}'")
                    query.first()
                    phone_id = query.value(0)

                    query.exec(f"delete from person_phone_junction where PersonId = {person_id} and PhoneNumberId = {phone_id}")
                    query.exec(f"delete from Phonenumbers where PhoneNumberId = {phone_id}")

            self.setup_phone_model()
        except Exception as e: handle_error(e)


    def delete_email(self):
        try:
            person_id = self.lineEditId.text()
            query = QSqlQuery()
            if len(self.listViewEmail.selectedIndexes()) >= 1:
                for items in (self.listViewEmail.selectedIndexes()):
                    email = (self.email_model.record(items.row()).field(0).value())
                    query.exec(f"SELECT EmailId FROM EmailQ  where PersonId = {person_id} and email = '{email}'")
                    query.first()
                    email_id = query.value(0)
                    query.exec(f"delete from person_email_junction where PersonId = {person_id} and EmailId = {email_id}")
                    query.exec(f"delete from Emails where EmailId = {email_id}")

            self.setup_email_model()
        except Exception as e: handle_error(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    make_a_expire_date()
    if os.path.isfile("hanso.txt"):
        if datetime.date(datetime.now()) >= get_expire_date() :
            vef_key, ok = QInputDialog().getText(window, "Expired :-(",
                                              "Your try has expired. Enter your license key:", QLineEdit.Normal)
            if ok and vef_key:
                if not verify_account_key(vef_key):
                    QtWidgets.QMessageBox.critical(None, 'Error','This key is not valid' )
                    sys.exit()
                else:
                    os.remove("hanso.txt")
                    QtWidgets.QMessageBox.information(None, 'Success','Your Software is acitvated, enjoy' )
            else:
                  sys.exit()    
    
    window.show()
    sys.exit(app.exec())
