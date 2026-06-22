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


ATTRIBUTION_DEFINITIONS = {
    '首次触点归因': '将成交全部归功于顾客首次验光的门店和验光师',
    '末次触点归因': '将成交全部归功于顾客最后一次成交的门店和验光师',
    '线性归因': '将成交平均分配给顾客所有到店记录对应的门店和验光师',
    '时间衰减归因': '距离成交时间越近的触点分配权重越高',
    '跨店归因': '分析顾客在不同门店验光和成交的归属关系',
    '线上补单归因': '将线上补单的成交归因为首次验光的门店和验光师',
}


def get_attribution_store_metrics(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return pd.DataFrame()
    
    store_names = sorted(valid['store_name'].unique().tolist())
    
    store_exam_counts = valid.groupby('store_name')['record_id'].nunique().to_dict()
    store_direct_deals = deals.groupby('store_name')['record_id'].nunique().to_dict()
    store_direct_revenue = deals.groupby('store_name')['effective_deal_price'].sum().to_dict()
    
    first_touch_deals = deals.groupby('attribution_first_touch_store')['record_id'].nunique().to_dict()
    first_touch_revenue = deals.groupby('attribution_first_touch_store')['effective_deal_price'].sum().to_dict()
    
    last_touch_deals = deals.groupby('attribution_last_touch_store')['record_id'].nunique().to_dict()
    last_touch_revenue = deals.groupby('attribution_last_touch_store')['effective_deal_price'].sum().to_dict()
    
    customer_visits_per_store = valid.groupby(['customer_id', 'store_name']).size().reset_index(name='visits')
    customer_total_visits = valid.groupby('customer_id').size().to_dict()
    
    customer_deals = deals.groupby('customer_id').size().to_dict()
    customer_deal_revenue = deals.groupby('customer_id')['effective_deal_price'].sum().to_dict()
    
    linear_attr = {}
    for store in store_names:
        store_customers = customer_visits_per_store[customer_visits_per_store['store_name'] == store]
        total_weight = 0.0
        for _, row in store_customers.iterrows():
            cid = row['customer_id']
            if cid in customer_deals:
                total_visits = customer_total_visits[cid]
                total_weight += customer_deals[cid] * (row['visits'] / total_visits)
        linear_attr[store] = round(total_weight, 2)
    
    deal_dates = deals.groupby('customer_id')['attr_first_deal_date'].first().to_dict()
    visit_dates = valid.groupby(['customer_id', 'store_name'])['exam_date'].apply(list).to_dict()
    
    time_decay_attr = {}
    for store in store_names:
        total_weight = 0.0
        store_customer_visits = valid[valid['store_name'] == store].groupby('customer_id')['exam_date'].apply(list).to_dict()
        for cid, dates in store_customer_visits.items():
            if cid in customer_deals and cid in deal_dates:
                total_visits = customer_total_visits[cid]
                deal_date = pd.to_datetime(deal_dates[cid])
                for visit_date_str in dates:
                    visit_date = pd.to_datetime(visit_date_str)
                    days_diff = abs((deal_date - visit_date).days)
                    weight = 1 / (1 + days_diff / 30)
                    total_weight += weight / total_visits
        time_decay_attr[store] = round(total_weight, 2)
    
    results = []
    for store in store_names:
        total_exams = store_exam_counts.get(store, 0)
        direct_deals = store_direct_deals.get(store, 0)
        direct_rev = store_direct_revenue.get(store, 0)
        ft_deals = first_touch_deals.get(store, 0)
        ft_rev = first_touch_revenue.get(store, 0)
        lt_deals = last_touch_deals.get(store, 0)
        lt_rev = last_touch_revenue.get(store, 0)
        lin_deals = linear_attr.get(store, 0)
        td_deals = time_decay_attr.get(store, 0)
        
        results.append({
            '门店': store,
            '门店验光数': total_exams,
            '门店直接成交数': direct_deals,
            '首次触点成交数': int(ft_deals),
            '末次触点成交数': int(lt_deals),
            '线性归因成交数': lin_deals,
            '时间衰减归因成交数': td_deals,
            '门店直接营收(元)': round(direct_rev, 2),
            '首次触点营收(元)': round(ft_rev, 2),
            '末次触点营收(元)': round(lt_rev, 2),
            '门店直接转化率(%)': round(direct_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '首次触点转化率(%)': round(ft_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '末次触点转化率(%)': round(lt_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '线性归因转化率(%)': round(lin_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '时间衰减转化率(%)': round(td_deals / total_exams * 100, 2) if total_exams > 0 else 0,
        })
    
    return pd.DataFrame(results)


def get_attribution_optometrist_metrics(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return pd.DataFrame()
    
    opt_names = sorted(valid['optometrist_name'].unique().tolist())
    
    results = []
    
    for opt in opt_names:
        opt_store = valid[valid['optometrist_name'] == opt]['store_name'].iloc[0]
        total_exams = valid[valid['optometrist_name'] == opt]['record_id'].nunique()
        
        first_touch_deals = deals[deals['attribution_first_touch_opt'] == opt]['record_id'].nunique()
        last_touch_deals = deals[deals['attribution_last_touch_opt'] == opt]['record_id'].nunique()
        same_opt_deals = deals[deals['optometrist_name'] == opt]['record_id'].nunique()
        
        first_touch_revenue = deals[deals['attribution_first_touch_opt'] == opt]['effective_deal_price'].sum()
        last_touch_revenue = deals[deals['attribution_last_touch_opt'] == opt]['effective_deal_price'].sum()
        same_opt_revenue = deals[deals['optometrist_name'] == opt]['effective_deal_price'].sum()
        
        results.append({
            '验光师': opt,
            '所属门店': opt_store,
            '验光数': total_exams,
            '直接成交数': same_opt_deals,
            '首次触点成交数': int(first_touch_deals),
            '末次触点成交数': int(last_touch_deals),
            '直接转化率(%)': round(same_opt_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '首次触点转化率(%)': round(first_touch_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '末次触点转化率(%)': round(last_touch_deals / total_exams * 100, 2) if total_exams > 0 else 0,
            '直接营收(元)': round(same_opt_revenue, 2),
            '首次触点营收(元)': round(first_touch_revenue, 2),
            '末次触点营收(元)': round(last_touch_revenue, 2),
        })
    
    return pd.DataFrame(results)


def get_cross_store_attribution_flow(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return pd.DataFrame()
    
    customers_with_deal = deals['customer_id'].unique()
    multi_visit_customers = valid[valid['customer_id'].isin(customers_with_deal)]
    multi_visit_customers = multi_visit_customers.groupby('customer_id').filter(lambda g: g['store_id'].nunique() > 1)
    
    if len(multi_visit_customers) == 0:
        return pd.DataFrame()
    
    flow_data = []
    for cid in multi_visit_customers['customer_id'].unique():
        customer_data = valid[valid['customer_id'] == cid].sort_values('exam_date')
        first_store = customer_data['store_name'].iloc[0]
        deal_stores = deals[deals['customer_id'] == cid]['store_name'].unique()
        total_deal_value = deals[deals['customer_id'] == cid]['effective_deal_price'].sum()
        
        for deal_store in deal_stores:
            deal_count = len(deals[(deals['customer_id'] == cid) & (deals['store_name'] == deal_store)])
            deal_value = deals[(deals['customer_id'] == cid) & (deals['store_name'] == deal_store)]['effective_deal_price'].sum()
            flow_data.append({
                'source': first_store,
                'target': deal_store,
                'value': deal_count,
                'revenue': deal_value,
                'customer_count': 1,
            })
    
    if not flow_data:
        return pd.DataFrame()
    
    flow_df = pd.DataFrame(flow_data)
    flow_df = flow_df.groupby(['source', 'target']).agg(
        成交数=('value', 'sum'),
        营收=('revenue', 'sum'),
        顾客数=('customer_count', 'sum'),
    ).reset_index()
    
    flow_df = flow_df.sort_values('成交数', ascending=False)
    return flow_df


def get_attribution_conversion_comparison(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    total_exams = len(valid)
    total_deals = len(deals)
    
    first_touch_deals = deals['attribution_first_touch_store'].notna().sum()
    last_touch_deals = deals['attribution_last_touch_store'].notna().sum()
    
    direct_deals = len(deals[deals['is_first_deal'] & (deals['store_name'] == deals['attribution_first_touch_store'])])
    
    cross_store_customers = deals[deals['is_exam_deal_diff_store']]['customer_id'].nunique()
    total_customers = deals['customer_id'].nunique()
    cross_store_ratio = cross_store_customers / total_customers * 100 if total_customers > 0 else 0
    
    online_customers = deals[deals['is_online_replenish']]['customer_id'].nunique()
    online_ratio = online_customers / total_customers * 100 if total_customers > 0 else 0
    
    avg_days_to_deal = deals['days_to_first_deal'].dropna().mean()
    
    data = [
        {'归因口径': '门店直接成交', '成交数': direct_deals, '转化率(%)': round(direct_deals / total_exams * 100, 2), '营收(元)': round(deals[deals['is_first_deal'] & (deals['store_name'] == deals['attribution_first_touch_store'])]['effective_deal_price'].sum(), 2)},
        {'归因口径': '首次触点归因', '成交数': total_deals, '转化率(%)': round(total_deals / total_exams * 100, 2), '营收(元)': round(deals['effective_deal_price'].sum(), 2)},
        {'归因口径': '末次触点归因', '成交数': total_deals, '转化率(%)': round(total_deals / total_exams * 100, 2), '营收(元)': round(deals['effective_deal_price'].sum(), 2)},
    ]
    
    summary = {
        '总验光数': total_exams,
        '总成交数': total_deals,
        '跨店成交顾客数': int(cross_store_customers),
        '跨店成交占比(%)': round(cross_store_ratio, 2),
        '线上补单顾客数': int(online_customers),
        '线上补单占比(%)': round(online_ratio, 2),
        '平均成交周期(天)': round(avg_days_to_deal, 1) if pd.notna(avg_days_to_deal) else 0,
    }
    
    return pd.DataFrame(data), summary


def get_lens_recommendation_effectiveness(df: pd.DataFrame, group_by: list = None) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    with_rec = valid[valid['lens_type_recommended'].notna()]
    
    if len(with_rec) == 0:
        return pd.DataFrame()
    
    group_cols = ['lens_subtype'] if group_by is None else ['lens_subtype'] + group_by
    group_cols = [c for c in group_cols if c in with_rec.columns]
    
    def _calc_metrics(g):
        total_rec = len(g)
        accepted = int(g['effective_deal'].sum())
        returned = int(g['is_return'].sum())
        after_sale = int(g['has_after_sale_flag'].sum())
        negative_after_sale = int(g['is_negative_after_sale'].sum())
        
        return pd.Series({
            '推荐数': total_rec,
            '成交数': accepted,
            '推荐接受率(%)': round(accepted / total_rec * 100, 2) if total_rec > 0 else 0,
            '退货数': returned,
            '退货率(%)': round(returned / accepted * 100, 2) if accepted > 0 else 0,
            '售后数': after_sale,
            '售后率(%)': round(after_sale / accepted * 100, 2) if accepted > 0 else 0,
            '负面售后数': negative_after_sale,
            '负面售后率(%)': round(negative_after_sale / accepted * 100, 2) if accepted > 0 else 0,
            '总营收(元)': round(g['effective_deal_price'].sum(), 2),
            '平均成交价(元)': round(g['effective_deal_price'].mean(), 2) if accepted > 0 else 0,
        })
    
    result = with_rec.groupby(group_cols, dropna=False).apply(_calc_metrics).reset_index()
    
    return result


def get_lens_effectiveness_by_age(df: pd.DataFrame) -> pd.DataFrame:
    return get_lens_recommendation_effectiveness(df, group_by=['age_group'])


def get_lens_effectiveness_by_prescription(df: pd.DataFrame) -> pd.DataFrame:
    return get_lens_recommendation_effectiveness(df, group_by=['prescription_degree_band'])


def get_lens_effectiveness_by_price_band(df: pd.DataFrame) -> pd.DataFrame:
    return get_lens_recommendation_effectiveness(df, group_by=['price_band'])


def get_lens_subtype_overview(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df['is_valid_record']]
    total_exams = len(valid)
    
    with_rec = valid[valid['lens_type_recommended'].notna()]
    
    if len(with_rec) == 0:
        return pd.DataFrame()
    
    lens_subtypes = with_rec['lens_subtype'].dropna().unique()
    
    results = []
    for subtype in lens_subtypes:
        subtype_data = with_rec[with_rec['lens_subtype'] == subtype]
        rec_count = len(subtype_data)
        deal_count = int(subtype_data['effective_deal'].sum())
        return_count = int(subtype_data['is_return'].sum())
        after_sale_count = int(subtype_data['has_after_sale_flag'].sum())
        total_revenue = subtype_data['effective_deal_price'].sum()
        avg_price = subtype_data['effective_deal_price'].mean()
        
        results.append({
            '镜片子类': subtype,
            '推荐数': rec_count,
            '推荐率(%)': round(rec_count / total_exams * 100, 2) if total_exams > 0 else 0,
            '成交数': deal_count,
            '接受率(%)': round(deal_count / rec_count * 100, 2) if rec_count > 0 else 0,
            '退货数': return_count,
            '退货率(%)': round(return_count / deal_count * 100, 2) if deal_count > 0 else 0,
            '售后数': after_sale_count,
            '售后率(%)': round(after_sale_count / deal_count * 100, 2) if deal_count > 0 else 0,
            '总营收(元)': round(total_revenue, 2),
            '平均成交价(元)': round(avg_price, 2) if deal_count > 0 else 0,
        })
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('推荐数', ascending=False)
    
    return result_df
