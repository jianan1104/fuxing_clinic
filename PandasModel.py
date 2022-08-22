from PyQt5 import QtCore, QtWidgets
import pandas as pd


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), isDoctorTable=False, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self._df = df
        self._isDoctorTable = isDoctorTable

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError,):
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except (IndexError,):
                return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                column_name = self.getColumnName(index)
                value = self._df.iloc[index.row(), index.column()]
                if isinstance(value, str):
                    return str(value)
                if isinstance(value, int):
                    return int(value)
                if isinstance(value, float):
                    return float(value)

                # if column_name in ['日期', '時段', '證號', '姓名']:
                #     return str(value)
                # else:
                #     return float(value)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole or role == QtCore.Qt.DecorationRole:
            column_name = self.getColumnName(index)
            if self._isDoctorTable:
                if column_name == '時數':
                    hours = value
                    range_salary = self._df.at[index.row(), '薪資級距']
                    doctor_pay = round((hours / 3.5) * range_salary, 0)
                    ppf_range = round((hours / 3.5) * 45, 0)
                    self._df.at[index.row(), 'PPF級距'] = ppf_range
                    check_number = self._df.at[index.row(), '核實人數']

                    if check_number > ppf_range:
                        ppf_pay = check_number - ppf_range
                        self._df.at[index.row(), 'PPF獎金'] = ppf_pay * 100

                    self._df.at[index.row(), '醫師診費'] = doctor_pay
                    if check_number > 0:
                        self._df.at[index.row(), '醫師薪水'] = self._df.at[index.row(), 'PPF獎金'] + self._df.at[
                            index.row(), '醫師診費']

            self._df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def getColumnsNames(self):
        return self._df.columns.tolist()

    def getColumnIndex(self, col):
        return self.getColumnsNames().index(col)

    def getColumnName(self, index):
        return self.getColumnsNames()[index.column()]
