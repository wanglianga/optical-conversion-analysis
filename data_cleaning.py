import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df = _mark_multiple_visits(df)
    df = _mark_cross_store_purchases(df)
    df = _handle_missing_prescription(df)
    df = _handle_returns(df)
    df = _handle_gift_orders(df)
    df = _handle_after_sale_repairs(df)
    df = _add_clean_flags(df)
    
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
    
    return summary


def get_abnormal_orders(df: pd.DataFrame) -> pd.DataFrame:
    cols = ['record_id', 'customer_id', 'customer_name', 'store_name', 
            'optometrist_name', 'exam_date', 'deal_made', 'deal_price',
            'is_return', 'is_gift', 'has_after_sale_flag', 'after_sale_type',
            'prescription_missing', 'data_quality_issue']
    
    abnormal = df[df['is_abnormal_order']][cols].copy()
    abnormal = abnormal.sort_values('data_quality_issue', ascending=False)
    
    return abnormal
