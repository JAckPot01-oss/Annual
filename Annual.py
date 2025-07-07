import streamlit as st
import pandas as pd


st.set_page_config(page_title="应收账款分析", layout="wide")

st.title("📊 应收账款分析系统（含千万客户与天杉明细）")
uploaded_file = st.file_uploader("📎 请上传原始 CSV 文件", type="csv")

if uploaded_file is not None:
    # 加载 CSV 文件
    df = pd.read_csv(uploaded_file, encoding='utf-8')
    df.columns = df.columns.str.strip().str.replace('\n', '', regex=True)

    # 清理空格并填充空值
    df['单位'] = df['单位'].ffill()
    df['客商名称'] = df['客商名称'].ffill().str.strip()  # 去除“客商名称”中的空格

    # 打印列名，帮助调试
    st.write("实际列名：", df.columns.tolist())

    # 修正字段名（确保与你的文件列名一致）
    columns_needed = ['单位', '客商名称', '应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']
    df = df[columns_needed]

    # 将金额字段转换为万元（除以10000）
    df[['应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']] = df[['应收账款总额', '1年内', '1_2', '2_3',
                                                                               '3_4', '4_5', '5年以上']] / 10000

    # 计算全院总应收账款（用于计算占比）
    total_all = df.groupby('客商名称')['应收账款总额'].sum().sum()

    # ------ 表1：千万以上客户统计 ------
    grouped = df.groupby('客商名称')[
        ['应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']].sum().reset_index()
    grouped = grouped[grouped['应收账款总额'] >= 1000]  # 过滤出应收账款大于等于1000万的客户
    grouped['占全院应收比重'] = grouped['应收账款总额'] / total_all  # 计算占全院应收账款的比重
    grouped = grouped.sort_values(by='应收账款总额', ascending=False)
    columns_ordered = ['客商名称', '占全院应收比重'] + ['应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']
    grouped = grouped[columns_ordered]

    # 添加“合计”行
    total_row = pd.DataFrame([{
        '客商名称': '合计',
        '占全院应收比重': grouped['占全院应收比重'].sum(),
        '应收账款总额': grouped['应收账款总额'].sum(),
        '1年内': grouped['1年内'].sum(),
        '1_2': grouped['1_2'].sum(),
        '2_3': grouped['2_3'].sum(),
        '3_4': grouped['3_4'].sum(),
        '4_5': grouped['4_5'].sum(),
        '5年以上': grouped['5年以上'].sum(),
    }])
    result1 = pd.concat([grouped, total_row], ignore_index=True)

    #-----Top3/5------------------
    # 修正字段名（确保与你的文件列名一致）
    columns_needed = ['单位', '客商名称', '应收账款总额',
                      '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']
    df = df[columns_needed]
    # 将所有金额字段转换为万元（除以10000）
    df[['应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']] = df[['应收账款总额', '1年内', '1_2', '2_3',
                                                                               '3_4', '4_5', '5年以上']]
    # 处理“研究中心”、“智能所”、“机电所”独立处理，合并“司法鉴定中心”和“检测中心”到“检测所”
    df['单位'] = df['单位'].replace({
        '研究中心': '研究中心',
        '智能所': '智能所',  # 修正为“智能所”
        '机电所': '机电所',
        '司法鉴定中心': '检测所',
        '检测中心': '检测所',
        '材料所': '材料所',
        '工业化所': '工业化所',
        '结构所': '结构所',
        '检测所': "检测所"
    })
    # 合并相同单位 + 客商名称，汇总账龄
    df_grouped = df.groupby(['单位', '客商名称'], as_index=False).sum()
    # 算每个单位的应收款项总额
    total_amount_per_unit = df_grouped.groupby('单位')['应收账款总额'].sum().reset_index()
    total_amount_per_unit.rename(columns={'应收账款总额': '单位总应收账款'}, inplace=True)
    # 处理“研究中心”、“智能所”、“机电所”取前三，其他单位取前五
    top3_units = ['研究中心', '智能所', '机电所']
    # 对于“研究中心”、“智能所”、“机电所”取前三客户
    top3 = (
        df_grouped[df_grouped['单位'].isin(top3_units)]  # 筛选出这3个单位
        .sort_values(['单位', '应收账款总额'], ascending=[True, False])  # 按“应收账款总额”降序排列
        .groupby('单位')
        .head(3)  # 每个单位取前三
    )
    # 对于“材料所”、“工业化所”和“结构所”取前五客户
    top5_units = ['材料所', '工业化所', '结构所']
    top5_special = (
        df_grouped[df_grouped['单位'].isin(top5_units)]  # 筛选出这3个单位
        .sort_values(['单位', '应收账款总额'], ascending=[True, False])  # 按“应收账款总额”降序排列
        .groupby('单位')
        .head(5)  # 每个单位取前五
    )
    # 对于其他单位取前五客户（包括合并后的“检测所”）
    top5_others = (
        df_grouped[~df_grouped['单位'].isin(top3_units + top5_units)]  # 筛选出非这3个单位
        .sort_values(['单位', '应收账款总额'], ascending=[True, False])  # 按“应收账款总额”降序排列
        .groupby('单位')
        .head(5)  # 每个单位取前五
    )
    # 合并前三、前五（材料所、工业化所、结构所）和其他单位的前五数据
    top_combined = pd.concat([top3, top5_special, top5_others])

    # 合并前3或前5客户数据和总应收账款
    top_combined = pd.merge(top_combined, total_amount_per_unit, on='单位', how='left')

    # 计算前3或前5客户的应收款项占比（前3或前5客户的总和占单位总应收账款的比例）
    top_combined['前客户占比'] = top_combined['应收账款总额'] / top_combined['单位总应收账款']
    st.subheader("✅ 每个单位前三或前五客户应收账款分析")
    st.dataframe(top_combined.style.format({'前客户占比': '{:.2%}'}), height=400)


    # ------ 表2：天杉类客户 ------
    df_tianshan = df[df['客商名称'].str.contains('天杉', na=False)]
    df_tianshan_grouped = df_tianshan.groupby('客商名称')[
        ['应收账款总额', '1年内', '1_2', '2_3', '3_4', '4_5', '5年以上']].sum().reset_index()
    df_tianshan_grouped['占全院应收比重'] = df_tianshan_grouped['应收账款总额'] / total_all
    df_tianshan_grouped = df_tianshan_grouped.sort_values(by='应收账款总额', ascending=False)
    df_tianshan_grouped = df_tianshan_grouped[columns_ordered]

    # 添加“合计”行
    tianshan_total = pd.DataFrame([{
        '客商名称': '合计',
        '占全院应收比重': df_tianshan_grouped['占全院应收比重'].sum(),
        '应收账款总额': df_tianshan_grouped['应收账款总额'].sum(),
        '1年内': df_tianshan_grouped['1年内'].sum(),
        '1_2': df_tianshan_grouped['1_2'].sum(),
        '2_3': df_tianshan_grouped['2_3'].sum(),
        '3_4': df_tianshan_grouped['3_4'].sum(),
        '4_5': df_tianshan_grouped['4_5'].sum(),
        '5年以上': df_tianshan_grouped['5年以上'].sum(),
    }])
    result2 = pd.concat([df_tianshan_grouped, tianshan_total], ignore_index=True)

    # ---- 展示结果 ----
    st.subheader("✅ 全院千万客户应收账款统计")
    st.dataframe(result1.style.format({'占全院应收比重': '{:.2%}'}), height=400)

    st.subheader("📌 天杉及其分子公司应收账款明细")
    st.dataframe(result2.style.format({'占全院应收比重': '{:.2%}'}), height=400)




    # ---- 下载按钮 ----
    def convert_df(df):
        return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')


    st.download_button("📥 下载表1：千万客户统计", convert_df(result1),
                       "全院客商千万以上应收账款统计.csv", "text/csv")
    st.download_button("📥 下载表2：天杉客户明细", convert_df(result2),
                       "天杉及其分子公司应收账款明细.csv", "text/csv")

    st.download_button("📥 下载前3或前5客户数据", convert_df(top_combined),
                       "每个单位前三或前五客户_含占比.csv", "text/csv")
