import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df = _mark_multiple_visits(df)
    df = _mark_cross_store_purchases(df)
    df = _add_price_band(df)
    df = _handle_missing_prescription(df)
    df = _handle_returns(df)
    df = _handle_gift_orders(df)
    df = _handle_after_sale_repairs(df)
    df = _add_attribution_markers(df)
    df = _add_clean_flags(df)
    
    return df


def _add_price_band(df: pd.DataFrame) -> pd.DataFrame:
    if 'price_band' not in df.columns:
        def _get_band(price):
            if pd.isna(price):
                return None
            if price < 500:
                return '0-500元'
            elif price < 1000:
                return '500-1000元'
            elif price < 2000:
                return '1000-2000元'
            elif price < 5000:
                return '2000-5000元'
            else:
                return '5000元以上'
        
        df['price_band'] = df['deal_price'].apply(_get_band)
        mask = df['price_band'].isna() & df['quoted_price'].notna()
        df.loc[mask, 'price_band'] = df.loc[mask, 'quoted_price'].apply(_get_band)
    
    return df


def _add_attribution_markers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['exam_date_dt'] = pd.to_datetime(df['exam_date'])
    
    customer_groups = df.groupby('customer_id')
    
    first_visit_info = customer_groups.agg(
        attr_first_visit_store_id=('store_id', 'first'),
        attr_first_visit_store_name=('store_name', 'first'),
        attr_first_visit_opt_id=('optometrist_id', 'first'),
        attr_first_visit_opt_name=('optometrist_name', 'first'),
        attr_first_visit_date=('exam_date_dt', 'min'),
        attr_total_visits=('record_id', 'count'),
    ).reset_index()
    
    deal_mask = df['effective_deal'] if 'effective_deal' in df.columns else df['deal_made']
    deal_groups = df[deal_mask].groupby('customer_id')
    first_deal_info = deal_groups.agg(
        attr_first_deal_store_id=('store_id', 'first'),
        attr_first_deal_store_name=('store_name', 'first'),
        attr_first_deal_opt_id=('optometrist_id', 'first'),
        attr_first_deal_opt_name=('optometrist_name', 'first'),
        attr_first_deal_date=('exam_date_dt', 'min'),
        attr_total_deals=('record_id', 'count'),
    ).reset_index()
    
    last_deal_info = deal_groups.agg(
        attr_last_deal_store_id=('store_id', 'last'),
        attr_last_deal_store_name=('store_name', 'last'),
        attr_last_deal_opt_id=('optometrist_id', 'last'),
        attr_last_deal_opt_name=('optometrist_name', 'last'),
        attr_last_deal_date=('exam_date_dt', 'max'),
    ).reset_index()
    
    df = df.merge(first_visit_info, on='customer_id', how='left')
    df = df.merge(first_deal_info, on='customer_id', how='left')
    df = df.merge(last_deal_info, on='customer_id', how='left')
    
    df['is_first_visit'] = df['exam_date_dt'] == df['attr_first_visit_date']
    df['is_first_deal'] = (df['exam_date_dt'] == df['attr_first_deal_date']) & df['deal_made']
    df['is_last_deal'] = (df['exam_date_dt'] == df['attr_last_deal_date']) & df['deal_made']
    
    df['attribution_first_touch_store'] = df['attr_first_visit_store_name']
    df['attribution_first_touch_opt'] = df['attr_first_visit_opt_name']
    df['attribution_last_touch_store'] = df['attr_last_deal_store_name']
    df['attribution_last_touch_opt'] = df['attr_last_deal_opt_name']
    
    df['is_exam_deal_same_store'] = df['attr_first_visit_store_id'] == df['attr_first_deal_store_id']
    df['is_exam_deal_diff_store'] = ~df['is_exam_deal_same_store'] & df['attr_first_deal_store_id'].notna()
    
    df['days_to_first_deal'] = (df['attr_first_deal_date'] - df['attr_first_visit_date']).dt.days
    
    if 'is_online_replenish' not in df.columns:
        df['is_online_replenish'] = False
    
    if 'channel' not in df.columns:
        df['channel'] = '门店验光'
        df.loc[df['is_online_replenish'], 'channel'] = '线上补单'
        df.loc[(df['visit_number'] > 1) & ~df['is_online_replenish'], 'channel'] = '门店复购'
    
    df['has_online_replenish'] = customer_groups['is_online_replenish'].transform('any').values
    
    df.drop(columns=['exam_date_dt'], inplace=True, errors='ignore')
    
    return df


def _mark_multiple_visits(df: pd.DataFrame) -> pd.DataFrame:
    customer_visits = df.groupby('customer_id').agg(
        total_visits=('record_id', 'count'),
        visit_store_count=('store_id', 'nunique'),
        first_visit_date=('exam_date', 'min'),
        last_visit_date=('exam_date', 'max')
    ).reset_index()
    
    customer_visits['is_return_customer'] = customer_visits['total_visits'] > 1
    customer_visits['days_between_visits'] = (
        pd.to_datetime(customer_visits['last_visit_date']) - 
        pd.to_datetime(customer_visits['first_visit_date'])
    ).dt.days
    
    df = df.merge(
        customer_visits[['customer_id', 'total_visits', 'visit_store_count', 
                        'is_return_customer', 'first_visit_date', 'last_visit_date',
                        'days_between_visits']],
        on='customer_id',
        how='left'
    )
    
    return df


def _mark_cross_store_purchases(df: pd.DataFrame) -> pd.DataFrame:
    def check_cross_store(group):
        stores = group['store_id'].unique()
        if len(stores) > 1:
            group['is_cross_store'] = True
            group['cross_store_count'] = len(stores)
            
            deal_records = group[group['deal_made'] == True]
            if len(deal_records) > 0:
                deal_stores = deal_records['store_id'].unique()
                group['has_cross_store_deal'] = len(deal_stores) > 1
            else:
                group['has_cross_store_deal'] = False
        else:
            group['is_cross_store'] = False
            group['cross_store_count'] = 1
            group['has_cross_store_deal'] = False
        return group
    
    df = df.groupby('customer_id', group_keys=False).apply(check_cross_store)
    
    return df


def _handle_missing_prescription(df: pd.DataFrame) -> pd.DataFrame:
    df['prescription_missing'] = ~df['has_prescription']
    
    df['prescription_missing_reason'] = '正常'
    df.loc[df['prescription_missing'] & (df['prescription_result'].isna()), 
           'prescription_missing_reason'] = '未完成验光'
    df.loc[df['prescription_missing'] & (df['deal_made'] == True), 
           'prescription_missing_reason'] = '无处方成交(异常)'
    
    return df


def _handle_returns(df: pd.DataFrame) -> pd.DataFrame:
    df['is_return'] = df['is_returned'].fillna(False)
    
    df['return_valid'] = False
    df.loc[df['is_return'] & df['deal_made'], 'return_valid'] = True
    df.loc[df['is_return'] & ~df['deal_made'], 'return_valid'] = False
    
    return df


def _handle_gift_orders(df: pd.DataFrame) -> pd.DataFrame:
    df['is_gift'] = df['is_gift_order'].fillna(False)
    
    df['gift_valid'] = False
    df.loc[df['is_gift'] & df['deal_made'], 'gift_valid'] = True
    
    df['effective_deal'] = df['deal_made'] & ~df['is_return'] & ~df['is_gift']
    df['effective_deal_price'] = np.where(
        df['effective_deal'],
        df['deal_price'],
        np.nan
    )
    
    return df


def _handle_after_sale_repairs(df: pd.DataFrame) -> pd.DataFrame:
    df['has_after_sale_flag'] = df['has_after_sale'].fillna(False)
    
    df['is_repair'] = df['after_sale_type'] == '返修'
    df['is_complaint'] = df['after_sale_type'] == '投诉处理'
    df['is_adjustment'] = df['after_sale_type'].isin(['镜架调整', '镜片磨损更换', '度数复查'])
    
    repair_types = ['返修', '退货退款', '投诉处理']
    df['is_negative_after_sale'] = df['after_sale_type'].isin(repair_types)
    
    return df


def _add_clean_flags(df: pd.DataFrame) -> pd.DataFrame:
    df['is_valid_record'] = True
    
    df['data_quality_issue'] = ''
    
    mask = df['prescription_missing'] & df['deal_made']
    df.loc[mask, 'data_quality_issue'] += '无处方成交;'
    df.loc[mask, 'is_valid_record'] = False
    
    mask = df['is_return'] & ~df['deal_made']
    df.loc[mask, 'data_quality_issue'] += '未成交却退货;'
    df.loc[mask, 'is_valid_record'] = False
    
    mask = df['is_gift'] & ~df['deal_made']
    df.loc[mask, 'data_quality_issue'] += '赠品但未成交;'
    df.loc[mask, 'is_valid_record'] = False
    
    mask = df['has_after_sale_flag'] & ~df['deal_made']
    df.loc[mask, 'data_quality_issue'] += '售后但未成交;'
    df.loc[mask, 'is_valid_record'] = False
    
    mask = df['quoted'] & df['quoted_price'].isna()
    df.loc[mask, 'data_quality_issue'] += '报价但无价格;'
    df.loc[mask, 'is_valid_record'] = False
    
    df['is_abnormal_order'] = df['data_quality_issue'] != ''
    
    return df


def get_cleaning_summary(df: pd.DataFrame) -> dict:
    total = len(df)
    
    summary = {
        '总记录数': total,
        '有效记录数': int(df['is_valid_record'].sum()),
        '异常记录数': int(df['is_abnormal_order'].sum()),
        '异常率': f"{df['is_abnormal_order'].mean() * 100:.2f}%",
        '多次到店顾客数': int(df[df['is_return_customer']]['customer_id'].nunique()),
        '跨店消费顾客数': int(df[df['is_cross_store']]['customer_id'].nunique()),
        '处方缺失记录数': int(df['prescription_missing'].sum()),
        '退货订单数': int(df['is_return'].sum()),
        '赠品订单数': int(df['is_gift'].sum()),
        '售后返修订单数': int(df['is_repair'].sum()),
        '负面售后订单数': int(df['is_negative_after_sale'].sum()),
    }
    
    if 'is_online_replenish' in df.columns:
        summary['线上补单记录数'] = int(df['is_online_replenish'].sum())
        summary['线上补单顾客数'] = int(df[df['is_online_replenish']]['customer_id'].nunique())
    
    if 'is_exam_deal_diff_store' in df.columns:
        customers_with_deal = df[df['effective_deal']]['customer_id'].unique()
        cross_store_deal = df[(df['is_exam_deal_diff_store']) & (df['customer_id'].isin(customers_with_deal))]['customer_id'].nunique()
        summary['验光成交跨店顾客数'] = int(cross_store_deal)
    
    if 'days_to_first_deal' in df.columns:
        avg_days = df['days_to_first_deal'].dropna().mean()
        summary['验光到首次成交平均天数'] = round(avg_days, 1) if pd.notna(avg_days) else 0
    
    return summary


def get_abnormal_orders(df: pd.DataFrame) -> pd.DataFrame:
    cols = ['record_id', 'customer_id', 'customer_name', 'store_name', 
            'optometrist_name', 'exam_date', 'deal_made', 'deal_price',
            'is_return', 'is_gift', 'has_after_sale_flag', 'after_sale_type',
            'prescription_missing', 'data_quality_issue']
    
    abnormal = df[df['is_abnormal_order']][cols].copy()
    abnormal = abnormal.sort_values('data_quality_issue', ascending=False)
    
    return abnormal
