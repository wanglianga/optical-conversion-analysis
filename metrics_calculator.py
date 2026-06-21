import pandas as pd
import numpy as np


METRIC_DEFINITIONS = {
    '验光总数': '所有完成验光登记的记录数',
    '有处方数': '验光后获得有效处方结果的记录数',
    '推荐数': '验光师给出镜片推荐方案的记录数',
    '试戴数': '顾客进行镜片或镜架试戴的记录数',
    '报价数': '销售人员给出正式报价的记录数',
    '成交数': '排除退货和赠品后的有效成交记录数',
    '验光成交转化率': '有效成交数 / 验光总数，反映整体转化效率',
    '处方推荐转化率': '推荐数 / 有处方数',
    '推荐试戴转化率': '试戴数 / 推荐数',
    '试戴报价转化率': '报价数 / 试戴数',
    '报价成交转化率': '成交数 / 报价数',
    '客单价(AOV)': '有效成交订单的平均成交金额',
    '镜片升级率': '推荐高端/防控镜片后成交的比例',
    '儿童近视防控接受度': '0-18岁青少年中选择防控镜片的成交比例',
    '复购率': '多次到店消费的顾客占总成交顾客的比例',
    '售后率': '成交订单中产生售后的比例',
    '返修率': '成交订单中需要返修的比例',
    '投诉率': '成交订单中产生投诉的比例',
}


def get_overall_metrics(df: pd.DataFrame) -> dict:
    valid = df[df['is_valid_record']]
    
    total_exam = len(valid)
    has_rx = int(valid['has_prescription'].sum())
    recommended = int(valid['lens_type_recommended'].notna().sum())
    tried_on = int(valid['tried_on'].sum())
    quoted = int(valid['quoted'].sum())
    deals = int(valid['effective_deal'].sum())
    
    total_revenue = valid['effective_deal_price'].sum()
    aov = total_revenue / deals if deals > 0 else 0
    
    return {
        '验光总数': total_exam,
        '有处方数': has_rx,
        '推荐数': recommended,
        '试戴数': tried_on,
        '报价数': quoted,
        '成交数': deals,
        '验光成交转化率': f"{(deals / total_exam * 100):.2f}%" if total_exam > 0 else "0%",
        '处方推荐转化率': f"{(recommended / has_rx * 100):.2f}%" if has_rx > 0 else "0%",
        '推荐试戴转化率': f"{(tried_on / recommended * 100):.2f}%" if recommended > 0 else "0%",
        '试戴报价转化率': f"{(quoted / tried_on * 100):.2f}%" if tried_on > 0 else "0%",
        '报价成交转化率': f"{(deals / quoted * 100):.2f}%" if quoted > 0 else "0%",
        '总营收(元)': round(total_revenue, 2),
        '客单价(AOV)': round(aov, 2),
    }


def get_conversion_funnel(df: pd.DataFrame, group_by: str = None) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    
    if group_by:
        results = []
        for name, group in valid.groupby(group_by):
            funnel = _calc_single_funnel(group)
            funnel[group_by] = name
            results.append(funnel)
        return pd.DataFrame(results)
    else:
        funnel = _calc_single_funnel(valid)
        return pd.DataFrame([funnel])


def _calc_single_funnel(group: pd.DataFrame) -> dict:
    total = len(group)
    has_rx = int(group['has_prescription'].sum())
    recommended = int(group['lens_type_recommended'].notna().sum())
    tried_on = int(group['tried_on'].sum())
    quoted = int(group['quoted'].sum())
    deals = int(group['effective_deal'].sum())
    
    return {
        '验光': total,
        '有处方': has_rx,
        '处方→推荐转化率(%)': round(recommended / has_rx * 100, 2) if has_rx > 0 else 0,
        '推荐': recommended,
        '推荐→试戴转化率(%)': round(tried_on / recommended * 100, 2) if recommended > 0 else 0,
        '试戴': tried_on,
        '试戴→报价转化率(%)': round(quoted / tried_on * 100, 2) if tried_on > 0 else 0,
        '报价': quoted,
        '报价→成交转化率(%)': round(deals / quoted * 100, 2) if quoted > 0 else 0,
        '成交': deals,
        '整体转化率(%)': round(deals / total * 100, 2) if total > 0 else 0,
        '总营收': round(group['effective_deal_price'].sum(), 2),
        '客单价': round(group['effective_deal_price'].mean(), 2) if deals > 0 else 0,
    }


def get_store_metrics(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    
    store_metrics = valid.groupby(['store_id', 'store_name', 'region']).apply(
        lambda g: pd.Series({
            '验光数': len(g),
            '成交数': int(g['effective_deal'].sum()),
            '转化率(%)': round(g['effective_deal'].mean() * 100, 2),
            '总营收': round(g['effective_deal_price'].sum(), 2),
            '客单价': round(g['effective_deal_price'].mean(), 2) if g['effective_deal'].sum() > 0 else 0,
            '平均检查项数': round(g['exam_items_count'].mean(), 2),
            '处方完整率(%)': round(g['has_prescription'].mean() * 100, 2),
            '试戴率(%)': round(g['tried_on'].mean() * 100, 2),
            '售后率(%)': round(g['has_after_sale_flag'].mean() * 100, 2) if g['effective_deal'].sum() > 0 else 0,
            '返修率(%)': round(g['is_repair'].mean() * 100, 2) if g['effective_deal'].sum() > 0 else 0,
            '复购顾客数': int(g[g['is_return_customer'] & g['effective_deal']]['customer_id'].nunique()),
            '成交顾客总数': int(g[g['effective_deal']]['customer_id'].nunique()),
        })
    ).reset_index()
    
    store_metrics['复购率(%)'] = round(
        store_metrics['复购顾客数'] / store_metrics['成交顾客总数'] * 100, 2
    ).replace([np.inf, -np.inf], 0).fillna(0)
    
    return store_metrics


def get_optometrist_metrics(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    
    opt_metrics = valid.groupby(['optometrist_id', 'optometrist_name', 'store_name', 
                                 'opt_cert_level', 'opt_seniority']).apply(
        lambda g: pd.Series({
            '验光数': len(g),
            '成交数': int(g['effective_deal'].sum()),
            '转化率(%)': round(g['effective_deal'].mean() * 100, 2),
            '总营收': round(g['effective_deal_price'].sum(), 2),
            '客单价': round(g['effective_deal_price'].mean(), 2) if g['effective_deal'].sum() > 0 else 0,
            '平均检查项数': round(g['exam_items_count'].mean(), 2),
            '处方完整率(%)': round(g['has_prescription'].mean() * 100, 2),
            '试戴率(%)': round(g['tried_on'].mean() * 100, 2),
            '推荐镜片数': int(g['lens_type_recommended'].notna().sum()),
            '高端镜片推荐率(%)': round(
                (g['lens_category'].isin(['高端', '防控'])).mean() * 100, 2
            ) if g['lens_type_recommended'].notna().sum() > 0 else 0,
            '售后率(%)': round(g['has_after_sale_flag'].mean() * 100, 2) if g['effective_deal'].sum() > 0 else 0,
        })
    ).reset_index()
    
    return opt_metrics


def get_lens_upgrade_rate(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    with_rec = valid[valid['lens_type_recommended'].notna()]
    
    upgrade = with_rec.groupby(['lens_category', 'lens_type_recommended']).apply(
        lambda g: pd.Series({
            '推荐数': len(g),
            '成交数': int(g['effective_deal'].sum()),
            '接受率(%)': round(g['effective_deal'].mean() * 100, 2),
            '总营收': round(g['effective_deal_price'].sum(), 2),
            '平均成交价': round(g['effective_deal_price'].mean(), 2) if g['effective_deal'].sum() > 0 else 0,
        })
    ).reset_index()
    
    category_totals = with_rec.groupby('lens_category').apply(
        lambda g: pd.Series({
            '推荐总数': len(g),
            '成交总数': int(g['effective_deal'].sum()),
            '分类接受率(%)': round(g['effective_deal'].mean() * 100, 2),
        })
    ).reset_index()
    
    upgrade = upgrade.merge(category_totals, on='lens_category', how='left')
    
    return upgrade


def get_myopia_control_acceptance(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    children = valid[valid['age_group'].isin(['0-12岁', '13-18岁'])]
    children_with_need = children[children['prescription_result'].isin(['轻度近视', '中度近视', '高度近视'])]
    
    if len(children_with_need) == 0:
        return pd.DataFrame()
    
    result = children_with_need.groupby(['age_group', 'prescription_result']).apply(
        lambda g: pd.Series({
            '目标人数': len(g),
            '推荐防控镜片数': int(g['is_myopia_control_lens'].sum()),
            '防控镜片成交数': int((g['is_myopia_control_lens'] & g['effective_deal']).sum()),
            '防控镜片推荐率(%)': round(g['is_myopia_control_lens'].mean() * 100, 2),
            '防控镜片接受率(%)': round(
                (g['is_myopia_control_lens'] & g['effective_deal']).sum() / 
                g['is_myopia_control_lens'].sum() * 100, 2
            ) if g['is_myopia_control_lens'].sum() > 0 else 0,
            '防控成交占比(%)': round(
                (g['is_myopia_control_lens'] & g['effective_deal']).sum() / 
                g['effective_deal'].sum() * 100, 2
            ) if g['effective_deal'].sum() > 0 else 0,
            '防控镜片营收': round(g[g['is_myopia_control_lens'] & g['effective_deal']]['effective_deal_price'].sum(), 2),
        })
    ).reset_index()
    
    return result


def get_category_matrix(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return pd.DataFrame()
    
    matrix = deals.pivot_table(
        index='age_group',
        columns='lens_category',
        values='effective_deal_price',
        aggfunc=['count', 'sum', 'mean'],
        fill_value=0
    )
    
    matrix.columns = [f'{col[1]}_{col[0]}' for col in matrix.columns]
    matrix = matrix.reset_index()
    
    return matrix


def get_after_sale_correlation(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return pd.DataFrame()
    
    corr_data = deals.groupby(['store_name', 'optometrist_name']).apply(
        lambda g: pd.Series({
            '成交数': len(g),
            '售后数': int(g['has_after_sale_flag'].sum()),
            '返修数': int(g['is_repair'].sum()),
            '投诉数': int(g['is_complaint'].sum()),
            '售后率(%)': round(g['has_after_sale_flag'].mean() * 100, 2),
            '返修率(%)': round(g['is_repair'].mean() * 100, 2),
            '投诉率(%)': round(g['is_complaint'].mean() * 100, 2),
            '平均客单价': round(g['effective_deal_price'].mean(), 2),
            '平均检查项数': round(g['exam_items_count'].mean(), 2),
        })
    ).reset_index()
    
    return corr_data


def get_age_group_metrics(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    
    age_metrics = valid.groupby('age_group').apply(
        lambda g: pd.Series({
            '验光数': len(g),
            '成交数': int(g['effective_deal'].sum()),
            '转化率(%)': round(g['effective_deal'].mean() * 100, 2),
            '总营收': round(g['effective_deal_price'].sum(), 2),
            '客单价': round(g['effective_deal_price'].mean(), 2) if g['effective_deal'].sum() > 0 else 0,
            '防控镜片占比(%)': round(
                g[g['effective_deal']]['is_myopia_control_lens'].mean() * 100, 2
            ) if g['effective_deal'].sum() > 0 else 0,
        })
    ).reset_index()
    
    age_order = ['0-12岁', '13-18岁', '19-30岁', '31-45岁', '46-60岁', '60岁以上']
    age_metrics['age_group'] = pd.Categorical(age_metrics['age_group'], categories=age_order, ordered=True)
    age_metrics = age_metrics.sort_values('age_group')
    
    return age_metrics


def get_all_metric_definitions() -> pd.DataFrame:
    df = pd.DataFrame([
        {'指标名称': k, '指标定义': v} for k, v in METRIC_DEFINITIONS.items()
    ])
    return df
