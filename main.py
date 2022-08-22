import sys
import xlwings as xw
import pandas as pd
from ui import Ui_MainWindow
from PyQt5.QtCore import pyqtSlot
from PandasModel import PandasModel
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QTableWidgetItem, QMessageBox
from fuxing import calculate_numbers


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("福星診所薪資計算工具");
        self.doctor_model = None
        self.doctor_df = None

    '''
    Doctor Salary Calculation
    '''

    @pyqtSlot()
    def on_btn_load_clicked(self):
        df = self.load_file()
        tab_index = self.tabWidget.currentIndex()
        if df:
            try:
                if tab_index == 2:
                    self.doctor_df = df
                    self.doctor_model = PandasModel(self.doctor_df, isDoctorTable=True)
                    self.doctor_model.dataChanged.connect(self.doctor_table_change)
                    self.tbv_doctor_m_report.setModel(self.doctor_model)
                    # for row in range(model.rowCount()):
                    #     c = QComboBox()
                    #     c.addItems(['3.5','3','2.5','2','1.5'])
                    #     i = self.tbv_doctor_m_report.model().index(row, model.getColumnIndex('時數'))
                    #     self.tbv_doctor_m_report.setIndexWidget(i,c)
                elif tab_index == 1:
                    _, check_df, non_check_df = calculate_numbers(df)
                    self.tbv_check.setModel(PandasModel(check_df))
                    self.tbv_non_check.setModel(PandasModel(non_check_df))
                    self.gb_check.setTitle(f'核實人數 {len(check_df)}人')
                    self.gb_non_check.setTitle(f'非核實人數 {len(non_check_df)}人')
                elif tab_index == 0:
                    self.xls2xlsx(df)
                    # self.tbv_all_report.setModel(PandasModel(df))
            except:
                QMessageBox.warning(self, '警告', '讀取失敗')

    @pyqtSlot()
    def doctor_table_change(self):
        summary = self.doctor_df.sum(numeric_only=True).drop(['日期', 'PPF級距', 'PPF獎金', '薪資級距']).tolist()
        for idx, data in enumerate(summary):
            item = QTableWidgetItem(f'{data}')
            self.tbw_doctor.setItem(0, idx, item)


    def load_file(self):
        tab_index = self.tabWidget.currentIndex()
        if tab_index != 0:
            fn, _ = QFileDialog.getOpenFileName(self, "Open File", "../", "報表檔案 (*.xlsx)");
            if fn:
                self.le_fp.setText(fn)
                df = pd.read_excel(fn)

                return df
        else:
            fp = str(QFileDialog.getExistingDirectory(self, "選擇月份報表目錄", "../"))
            if fp:
                return fp

    def xls2xlsx(self, files):
        for fp in files:
            wb = xw.Book(fp)
            fn = fp[:-4] + '.xlsx'
            wb.save(f'{fn}')
            wb.close()
            self.statusbar.showMessage(f'Save File {fn}.')
        QMessageBox.information(self, '通知', f'轉檔成功')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
