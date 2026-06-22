import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

STORES = [
    {'store_id': 'S001', 'store_name': '北京朝阳大悦城店', 'region': '华北', 'opening_date': '2020-03-15'},
    {'store_id': 'S002', 'store_name': '上海陆家嘴店', 'region': '华东', 'opening_date': '2019-08-20'},
    {'store_id': 'S003', 'store_name': '广州天河城店', 'region': '华南', 'opening_date': '2021-01-10'},
    {'store_id': 'S004', 'store_name': '深圳万象城店', 'region': '华南', 'opening_date': '2020-11-05'},
    {'store_id': 'S005', 'store_name': '成都春熙路店', 'region': '西南', 'opening_date': '2022-02-18'},
    {'store_id': 'S006', 'store_name': '杭州西湖银泰店', 'region': '华东', 'opening_date': '2021-06-30'},
]

OPTOMETRISTS = [
    {'opt_id': 'O001', 'opt_name': '张明', 'store_id': 'S001', 'seniority': 8, 'cert_level': '高级'},
    {'opt_id': 'O002', 'opt_name': '李芳', 'store_id': 'S001', 'seniority': 3, 'cert_level': '中级'},
    {'opt_id': 'O003', 'opt_name': '王伟', 'store_id': 'S002', 'seniority': 12, 'cert_level': '高级'},
    {'opt_id': 'O004', 'opt_name': '陈静', 'store_id': 'S002', 'seniority': 5, 'cert_level': '中级'},
    {'opt_id': 'O005', 'opt_name': '刘洋', 'store_id': 'S003', 'seniority': 6, 'cert_level': '高级'},
    {'opt_id': 'O006', 'opt_name': '赵雪', 'store_id': 'S003', 'seniority': 2, 'cert_level': '初级'},
    {'opt_id': 'O007', 'opt_name': '孙磊', 'store_id': 'S004', 'seniority': 10, 'cert_level': '高级'},
    {'opt_id': 'O008', 'opt_name': '周琳', 'store_id': 'S004', 'seniority': 4, 'cert_level': '中级'},
    {'opt_id': 'O009', 'opt_name': '吴强', 'store_id': 'S005', 'seniority': 7, 'cert_level': '高级'},
    {'opt_id': 'O010', 'opt_name': '郑丽', 'store_id': 'S005', 'seniority': 1, 'cert_level': '初级'},
    {'opt_id': 'O011', 'opt_name': '钱浩', 'store_id': 'S006', 'seniority': 9, 'cert_level': '高级'},
    {'opt_id': 'O012', 'opt_name': '冯婷', 'store_id': 'S006', 'seniority': 3, 'cert_level': '中级'},
]

LENS_TYPES = [
    {'lens_type': '单光镜片', 'lens_category': '基础', 'base_price': 300, 'is_myopia_control': False, 'lens_subtype': '基础镜片'},
    {'lens_type': '防蓝光镜片', 'lens_category': '功能', 'base_price': 680, 'is_myopia_control': False, 'lens_subtype': '防蓝光'},
    {'lens_type': '渐进多焦点镜片', 'lens_category': '高端', 'base_price': 1580, 'is_myopia_control': False, 'lens_subtype': '渐进多焦点'},
    {'lens_type': '双光镜片', 'lens_category': '功能', 'base_price': 880, 'is_myopia_control': False, 'lens_subtype': '多焦点'},
    {'lens_type': '高折射镜片(1.67)', 'lens_category': '高端', 'base_price': 1280, 'is_myopia_control': False, 'lens_subtype': '高折射'},
    {'lens_type': '高折射镜片(1.74)', 'lens_category': '高端', 'base_price': 2680, 'is_myopia_control': False, 'lens_subtype': '高折射'},
    {'lens_type': '角膜塑形镜(OK镜)', 'lens_category': '防控', 'base_price': 8800, 'is_myopia_control': True, 'lens_subtype': '儿童控制'},
    {'lens_type': '离焦框架镜片', 'lens_category': '防控', 'base_price': 3200, 'is_myopia_control': True, 'lens_subtype': '儿童控制'},
    {'lens_type': '渐变太阳镜片', 'lens_category': '功能', 'base_price': 980, 'is_myopia_control': False, 'lens_subtype': '功能镜片'},
    {'lens_type': '偏光镜片', 'lens_category': '功能', 'base_price': 780, 'is_myopia_control': False, 'lens_subtype': '功能镜片'},
]

AGE_GROUPS = ['0-12岁', '13-18岁', '19-30岁', '31-45岁', '46-60岁', '60岁以上']
EXAM_ITEMS = ['电脑验光', '主觉验光', '散瞳验光', '眼轴测量', '角膜地形图', '眼压测量', '眼底检查']
PRESCRIPTION_RESULTS = ['轻度近视', '中度近视', '高度近视', '远视', '散光', '老花', '正常视力']
AFTER_SALE_TYPES = ['镜片磨损更换', '镜架调整', '度数复查', '返修', '退货退款', '赠品补发', '投诉处理']
PRICE_BANDS = ['0-500元', '500-1000元', '1000-2000元', '2000-5000元', '5000元以上']
CHANNELS = ['门店验光', '线上补单', '门店复购']
LENS_SUBTYPES = ['基础镜片', '防蓝光', '渐进多焦点', '多焦点', '高折射', '儿童控制', '功能镜片']


def generate_customers(n=2000):
    first_names = ['张', '李', '王', '刘', '陈', '杨', '黄', '赵', '吴', '周', '徐', '孙', '马', '朱', '胡']
    last_names = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀英', '霞', '平']
    
    customers = []
    for i in range(n):
        age = int(np.random.normal(35, 18))
        age = max(5, min(85, age))
        if age <= 12:
            age_group = '0-12岁'
        elif age <= 18:
            age_group = '13-18岁'
        elif age <= 30:
            age_group = '19-30岁'
        elif age <= 45:
            age_group = '31-45岁'
        elif age <= 60:
            age_group = '46-60岁'
        else:
            age_group = '60岁以上'
        
        phone = f'138{np.random.randint(1000, 9999):04d}{np.random.randint(1000, 9999):04d}'
        name = random.choice(first_names) + random.choice(last_names)
        
        customers.append({
            'customer_id': f'C{i+1:05d}',
            'customer_name': name,
            'phone': phone,
            'age': age,
            'age_group': age_group,
            'gender': np.random.choice(['男', '女'], p=[0.48, 0.52]),
        })
    
    return pd.DataFrame(customers)


def _generate_sphere_degree(prescription_result, age):
    if prescription_result == '轻度近视':
        return round(np.random.uniform(-3.0, -0.5), 2)
    elif prescription_result == '中度近视':
        return round(np.random.uniform(-6.0, -3.0), 2)
    elif prescription_result == '高度近视':
        return round(np.random.uniform(-12.0, -6.0), 2)
    elif prescription_result == '远视':
        return round(np.random.uniform(0.5, 4.0), 2)
    elif prescription_result == '老花':
        add_degree = round(np.random.uniform(0.75, 3.0), 2)
        return add_degree
    elif prescription_result == '散光':
        return round(np.random.uniform(-2.0, -0.5), 2)
    else:
        return 0.0


def _generate_cylinder_degree(prescription_result):
    if prescription_result == '散光':
        return round(np.random.uniform(-2.5, -0.5), 2)
    elif prescription_result in ['轻度近视', '中度近视', '高度近视']:
        if np.random.random() < 0.6:
            return round(np.random.uniform(-1.5, -0.25), 2)
        return 0.0
    else:
        return 0.0


def _get_price_band(price):
    if price is None or pd.isna(price):
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


def generate_records(customers_df, n_records=3800):
    records = []
    customers = customers_df.to_dict('records')
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 20)
    date_range = (end_date - start_date).days
    
    customer_visit_count = {}
    customer_first_exam_store = {}
    customer_first_exam_opt = {}
    
    for i in range(n_records):
        customer = random.choice(customers)
        cid = customer['customer_id']
        customer_visit_count[cid] = customer_visit_count.get(cid, 0) + 1
        visit_num = customer_visit_count[cid]
        
        if visit_num == 1:
            days_offset = np.random.randint(0, date_range)
            exam_date = start_date + timedelta(days=days_offset)
            store = random.choice(STORES)
            store_optometrists = [o for o in OPTOMETRISTS if o['store_id'] == store['store_id']]
            opt = random.choice(store_optometrists)
            customer_first_exam_store[cid] = store
            customer_first_exam_opt[cid] = opt
            channel = '门店验光'
            is_online_replenish = False
        else:
            prev_date = start_date
            prev_records = [r for r in records if r['customer_id'] == cid]
            if prev_records:
                prev_date = datetime.strptime(prev_records[-1]['exam_date'], '%Y-%m-%d')
            
            days_after_prev = np.random.randint(3, 180)
            exam_date = prev_date + timedelta(days=days_after_prev)
            if exam_date > end_date:
                exam_date = end_date - timedelta(days=np.random.randint(1, 30))
            
            channel_rand = np.random.random()
            if channel_rand < 0.15:
                channel = '线上补单'
                is_online_replenish = True
                store = customer_first_exam_store[cid]
                opt = customer_first_exam_opt[cid]
            elif channel_rand < 0.35:
                other_stores = [s for s in STORES if s['store_id'] != customer_first_exam_store[cid]['store_id']]
                if other_stores:
                    store = random.choice(other_stores)
                    store_optometrists = [o for o in OPTOMETRISTS if o['store_id'] == store['store_id']]
                    opt = random.choice(store_optometrists)
                else:
                    store = customer_first_exam_store[cid]
                    opt = customer_first_exam_opt[cid]
                channel = '门店复购'
                is_online_replenish = False
            else:
                store = customer_first_exam_store[cid]
                opt = customer_first_exam_opt[cid]
                channel = '门店复购'
                is_online_replenish = False
        
        exam_items_count = np.random.randint(2, 6)
        exam_items = random.sample(EXAM_ITEMS, exam_items_count)
        if is_online_replenish:
            exam_items_count = 1
            exam_items = '线上复查'
        
        has_prescription = np.random.random() > 0.08 or visit_num > 1
        
        if has_prescription:
            age = customer['age']
            if age <= 18:
                prescript_probs = [0.2, 0.35, 0.15, 0.05, 0.2, 0.0, 0.05]
            elif age >= 45:
                prescript_probs = [0.1, 0.15, 0.1, 0.1, 0.15, 0.3, 0.1]
            else:
                prescript_probs = [0.25, 0.25, 0.1, 0.08, 0.2, 0.05, 0.07]
            prescription = np.random.choice(PRESCRIPTION_RESULTS, p=prescript_probs)
            sphere_degree = _generate_sphere_degree(prescription, age)
            cylinder_degree = _generate_cylinder_degree(prescription)
        else:
            prescription = None
            sphere_degree = None
            cylinder_degree = None
        
        tried_on = np.random.random() > 0.15 or is_online_replenish
        
        if prescription and prescription != '正常视力':
            quoted = True
            lens = random.choice(LENS_TYPES)
            
            if customer['age_group'] in ['0-12岁', '13-18岁'] and lens['is_myopia_control']:
                lens_accept_prob = 0.55
            else:
                lens_accept_prob = 0.7 if lens['lens_category'] == '基础' else 0.45
            
            if is_online_replenish:
                lens_accept_prob *= 1.1
            
            price_factor = np.random.normal(1.0, 0.15)
            quoted_price = max(lens['base_price'] * 0.7, lens['base_price'] * price_factor)
            quoted_price = round(quoted_price, 0)
            
            deal_made = np.random.random() < lens_accept_prob and tried_on
            
            is_gift = False
            is_returned = False
            
            if deal_made:
                deal_price = round(quoted_price * np.random.uniform(0.85, 1.0), 0)
                is_gift = np.random.random() < 0.03
                if is_gift:
                    deal_price = 0
                
                if np.random.random() < 0.06:
                    is_returned = True
                
                repurchase = visit_num > 1
            else:
                deal_price = None
                repurchase = False
            
            price_band = _get_price_band(deal_price if deal_made else quoted_price)
            lens_subtype = lens.get('lens_subtype', None)
        else:
            quoted = False
            lens = {'lens_type': None, 'lens_category': None, 'is_myopia_control': False, 'lens_subtype': None}
            quoted_price = None
            deal_made = False
            deal_price = None
            is_gift = False
            is_returned = False
            repurchase = False
            price_band = None
            lens_subtype = None
        
        has_after_sale = False
        after_sale_type = None
        after_sale_date = None
        if deal_made and not is_returned and np.random.random() < 0.12:
            has_after_sale = True
            after_sale_type = np.random.choice(AFTER_SALE_TYPES, p=[0.25, 0.2, 0.2, 0.15, 0.0, 0.1, 0.1])
            after_sale_date = exam_date + timedelta(days=np.random.randint(1, 180))
        
        records.append({
            'record_id': f'R{i+1:06d}',
            'customer_id': cid,
            'customer_name': customer['customer_name'],
            'phone': customer['phone'],
            'age': customer['age'],
            'age_group': customer['age_group'],
            'gender': customer['gender'],
            'visit_number': visit_num,
            'exam_date': exam_date.strftime('%Y-%m-%d'),
            'channel': channel,
            'is_online_replenish': is_online_replenish,
            'store_id': store['store_id'],
            'store_name': store['store_name'],
            'region': store['region'],
            'optometrist_id': opt['opt_id'],
            'optometrist_name': opt['opt_name'],
            'opt_seniority': opt['seniority'],
            'opt_cert_level': opt['cert_level'],
            'exam_items': '、'.join(exam_items) if isinstance(exam_items, list) else exam_items,
            'exam_items_count': exam_items_count,
            'has_prescription': has_prescription,
            'prescription_result': prescription,
            'sphere_degree': sphere_degree,
            'cylinder_degree': cylinder_degree,
            'lens_type_recommended': lens['lens_type'],
            'lens_category': lens['lens_category'],
            'lens_subtype': lens_subtype,
            'is_myopia_control_lens': lens['is_myopia_control'],
            'tried_on': tried_on,
            'quoted': quoted,
            'quoted_price': quoted_price,
            'deal_made': deal_made,
            'deal_price': deal_price,
            'price_band': price_band,
            'is_gift_order': is_gift,
            'is_returned': is_returned,
            'repurchase_customer': repurchase,
            'has_after_sale': has_after_sale,
            'after_sale_type': after_sale_type,
            'after_sale_date': after_sale_date.strftime('%Y-%m-%d') if after_sale_date else None,
        })
    
    df = pd.DataFrame(records)
    return df


def generate_all_data():
    customers_df = generate_customers(2000)
    records_df = generate_records(customers_df, 3500)
    
    customers_df.to_csv('data/customers.csv', index=False, encoding='utf-8-sig')
    records_df.to_csv('data/optical_records.csv', index=False, encoding='utf-8-sig')
    
    stores_df = pd.DataFrame(STORES)
    opt_df = pd.DataFrame(OPTOMETRISTS)
    lens_df = pd.DataFrame(LENS_TYPES)
    
    stores_df.to_csv('data/stores.csv', index=False, encoding='utf-8-sig')
    opt_df.to_csv('data/optometrists.csv', index=False, encoding='utf-8-sig')
    lens_df.to_csv('data/lens_types.csv', index=False, encoding='utf-8-sig')
    
    print(f'数据生成完成:')
    print(f'  顾客数据: {len(customers_df)} 条')
    print(f'  验光记录: {len(records_df)} 条')
    print(f'  门店数据: {len(stores_df)} 条')
    print(f'  验光师数据: {len(opt_df)} 条')
    print(f'  镜片类型: {len(lens_df)} 条')
    
    return customers_df, records_df, stores_df, opt_df, lens_df


if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    generate_all_data()
