import pandas as pd
import numpy as np
import glob
import os


def calculate_numbers(df: pd.DataFrame()) -> float:
    """
    計算核實人數
    """
    patient_list = df[~df['醫'].isnull()]

    money_string_list = ['掛號費', '自付費']
    self_pay_string_list = ['掛號費', '自付費', '自費', '押金']

    # money condition
    sum_of_money = patient_list[money_string_list].astype(int).sum(axis=1)
    sum_of_all_money = patient_list[self_pay_string_list].astype(int).sum(axis=1)

    over_zero = sum_of_money > 0
    no_payment = sum_of_money == 0
    in_range = sum_of_money < 500

    # card index condition
    card_index = patient_list['卡'].astype(str)
    have_card_index = ~card_index.isnull()
    no_card_index = card_index.isnull()
    vu_index = card_index == 'VU'

    # all money condition
    sum_of_all_money = patient_list[self_pay_string_list].astype(int).sum(axis=1)
    over_range = sum_of_all_money >= 500

    # info condition
    info = patient_list['說明'].astype(str)
    d_card = info.str.contains('D刷').fillna(False)
    deposit_full = info.str.contains('押滿').fillna(False)

    without_special_case = ~(info.str.contains("優待|還卡|補刷|醫證|A視訊").fillna(False)) & ~(
        card_index.str.contains("HV").fillna(False))

    # list 卡序=HV=0

    # con1: 掛號費＋自付費 > 0 & 有卡序
    con1 = patient_list[over_zero & have_card_index & without_special_case]

    # con2: 掛號費＋自付費 = 0 & 有卡序 & 卡序沒有VU或D刷
    con2 = patient_list[have_card_index & no_payment & ~vu_index & ~d_card & without_special_case]

    # con3: 卡序是VU
    con3 = patient_list[vu_index & without_special_case]

    # con4: 沒有卡序 & 掛號費＋自付費＋自費＋押金 >= 500 or 卡序有押滿
    con4 = patient_list[no_card_index & (over_range | deposit_full) & without_special_case]
    # con4 = con4[without_special_case]

    # con5: 有卡序 & 掛號費＋自付費 = 0 & 卡序是D刷
    con5 = patient_list[have_card_index & no_payment & d_card & without_special_case]

    final_check_number = len(con1) + len(con2) * 0.5 + len(con3) + len(con4) + len(con5)

    check_df = pd.concat([con1, con2, con3, con4, con5])
    non_check_index = list(set(patient_list.index.tolist()) - set(check_df.index.tolist()))
    non_check_df = df.iloc[non_check_index]

    return final_check_number, check_df, non_check_df


class FuXing():

    def __init__(self, fp=None):
        self._fp = fp
        self.files = sorted(glob.glob(self._fp))
        self.doctor_list = self.get_all_doctor_list(self.files)

    def get_all_doctor_list(self) -> list:
        doctor_list = []
        for fp in self.files:
            df = pd.read_excel(fp)
            doctors = df[~df['醫'].isnull()]['醫'].drop_duplicates().tolist()
            doctor_list.extend(doctors)

        return list(set(doctor_list))

    def get_status(self, df: pd.DataFrame(), single_doctor=False) -> dict:
        if single_doctor:
            date = df['日期'].iloc[0]
            patient_number = len(df)
            registration_fee = pd.to_numeric(df['掛號費']).sum()
            partial_burden = pd.to_numeric(df['自付費']).sum()
            self_pay = pd.to_numeric(df['自費']).sum()
            security_deposit = pd.to_numeric(df['押金']).sum()
            drug_burden = pd.to_numeric(df['藥自付']).sum()
            arrears = pd.to_numeric(df['欠款']).sum()
            repayment = pd.to_numeric(df['還款']).sum()
            period = df['段'].drop_duplicates().tolist()
        else:
            result_index = df.index[df['證號'] == '總計:'].tolist()[0]
            date = df.at[result_index - 1, '日期']
            patient_number = int(df.at[result_index, '姓名'].strip().replace('人', ''))
            registration_fee = int(df.at[result_index, '掛號費'].strip())
            partial_burden = int(df.at[result_index, '自付費'].strip())
            self_pay = int(df.at[result_index, '自費'].strip())
            security_deposit = int(df.at[result_index, '押金'].strip())
            drug_burden = int(df.at[result_index, '藥自付'].strip())
            arrears = int(df.at[result_index, '欠款'])
            repayment = int(df.at[result_index, '還款'])
            period = df[~df['段'].isnull()]['段'].drop_duplicates().tolist()

        if len(period) != 1:
            print('此報表包含多個時段的資訊，請再重新確認！')
        else:
            period = period[0]
            if period == 'S':
                period = '早上'
            elif period == 'T':
                period = '下午'
            elif period == 'U':
                period = '晚上'

        data = {
            '日期': str(f'{date:7}'),
            '時段': str(period),
            '病人總數': int(patient_number),
            '掛號費': int(registration_fee),
            '自付費': int(partial_burden),
            '自費': int(self_pay),
            '押金': int(security_deposit),
            '藥自付': int(drug_burden),
            '欠款': int(arrears),
            '還款': int(repayment),
        }

        return data

    def getAllReport(self, save=True):
        report = []
        month = self.files[0][-11:-9]
        for idx, file in enumerate(self.files):
            try:
                df = pd.read_excel(file)
                data = self.get_status(df, plot=False)
                number = calculate_numbers(df)
                data['核實人數'] = int(number)
                report.append(data)
            except:
                print(f'Get Error: \t{file}')

        df_report = pd.DataFrame(report)
        df_report = df_report.append(df_report.sum(numeric_only=True), ignore_index=True)
        if save:
            df_report.to_excel(f'{month}月總報表.xlsx', index=False)
        return df_report

    def get_doctor_report(self, save=True):
        doctor_report = []
        for doctor in self.doctor_list:
            error = False
            report = []
            month = self.files[0][-11:-9]
            for idx, file in enumerate(self.files):
                df = pd.read_excel(file)
                df = df[df['醫'] == doctor]
                if len(df) == 0:
                    continue
                else:
                    try:
                        data = self.get_status(df, plot=False, single_doctor=True)
                        number = calculate_numbers(df)
                        data['核實人數'] = float(number)
                        report.append(data)
                    except:
                        error = True
                        print(f'Get Error: \t{file}')

            df_report = pd.DataFrame(report)
            df_report['時數'] = 0

            df_report.loc[df_report['核實人數'] > 30, '薪資級距'] = 4500
            df_report.loc[(df_report['核實人數'] <= 30) & (df_report['核實人數'] > 25), '薪資級距'] = 4200
            df_report.loc[(df_report['核實人數'] <= 25) & (df_report['核實人數'] > 20), '薪資級距'] = 4200
            df_report.loc[(df_report['核實人數'] <= 20) & (df_report['核實人數'] > 15), '薪資級距'] = 3600
            df_report.loc[(df_report['核實人數'] <= 15) & (df_report['核實人數'] > 10), '薪資級距'] = 3300
            df_report.loc[df_report['核實人數'] <= 10, '薪資級距'] = 3000
            df_report['醫師診費'] = 0
            df_report['PPF級距'] = 45
            df_report['PPF獎金'] = 0
            df_report['醫師薪水'] = 0

            doctor_report.append(df_report)
            if save & ~error:
                df_report.to_excel(f'醫師{int(doctor)}-{month}月總報表.xlsx', index=False)

        return doctor_report
