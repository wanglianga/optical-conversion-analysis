import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLOR_SCHEME = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'warning': '#d62728',
    'info': '#9467bd',
    '防控': '#e377c2',
    '高端': '#7f7f7f',
    '功能': '#bcbd22',
    '基础': '#17becf',
}


def create_store_comparison_chart(store_metrics: pd.DataFrame):
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('门店验光数 vs 成交数', '门店转化率对比', 
                        '门店总营收对比', '门店客单价对比'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    fig.add_trace(
        go.Bar(x=store_metrics['store_name'], y=store_metrics['验光数'], 
               name='验光数', marker_color=COLOR_SCHEME['primary']),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=store_metrics['store_name'], y=store_metrics['成交数'], 
               name='成交数', marker_color=COLOR_SCHEME['success']),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=store_metrics['store_name'], y=store_metrics['转化率(%)'],
               name='转化率(%)', marker_color=COLOR_SCHEME['secondary']),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=store_metrics['store_name'], y=store_metrics['总营收'],
               name='总营收(元)', marker_color=COLOR_SCHEME['info']),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(x=store_metrics['store_name'], y=store_metrics['客单价'],
               name='客单价(元)', marker_color=COLOR_SCHEME['warning']),
        row=2, col=2
    )
    
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text='门店综合对比分析',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif')
    )
    
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(tickangle=30, row=i, col=j)
    
    return fig


def create_optometrist_funnel(opt_metrics: pd.DataFrame, top_n: int = 12):
    sorted_opt = opt_metrics.sort_values('验光数', ascending=False).head(top_n)
    
    stages = ['验光', '有处方', '推荐', '试戴', '报价', '成交']
    
    fig = go.Figure()
    
    for _, row in sorted_opt.iterrows():
        opt_name = row['optometrist_name']
        exam_count = row['验光数']
        conversion_rate = row['转化率(%)'] / 100
        
        prescription_rate = row['处方完整率(%)'] / 100
        tryon_rate = row['试戴率(%)'] / 100
        
        values = [
            exam_count,
            int(exam_count * prescription_rate),
            row['推荐镜片数'],
            int(exam_count * tryon_rate),
            int(row['推荐镜片数'] * 0.85),
            row['成交数']
        ]
        
        fig.add_trace(go.Scatter(
            x=stages,
            y=values,
            mode='lines+markers',
            name=f"{opt_name}({row['store_name']})",
            hovertemplate=f"{opt_name}<br>%{{x}}: %{{y}}人<extra></extra>"
        ))
    
    fig.update_layout(
        title=f'验光师转化漏斗对比 (Top {top_n})',
        title_x=0.5,
        height=600,
        xaxis_title='转化阶段',
        yaxis_title='人数',
        hovermode='x unified',
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5)
    )
    
    return fig


def create_category_matrix(category_matrix: pd.DataFrame):
    if category_matrix.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    count_cols = [c for c in category_matrix.columns if c.endswith('_count')]
    sum_cols = [c for c in category_matrix.columns if c.endswith('_sum')]
    
    count_data = category_matrix[['age_group'] + count_cols].copy()
    count_data.columns = ['年龄段'] + [c.replace('_count', '') for c in count_cols]
    count_data = count_data.set_index('年龄段')
    
    fig = px.imshow(
        count_data,
        text_auto=True,
        aspect='auto',
        color_continuous_scale='Blues',
        title='年龄段 × 镜片品类 成交数量矩阵'
    )
    
    fig.update_layout(
        height=500,
        xaxis_title='镜片品类',
        yaxis_title='年龄段',
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        title_x=0.5
    )
    
    return fig


def create_lens_upgrade_chart(upgrade_metrics: pd.DataFrame):
    if upgrade_metrics.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = px.bar(
        upgrade_metrics,
        x='lens_type_recommended',
        y='接受率(%)',
        color='lens_category',
        color_discrete_map=COLOR_SCHEME,
        hover_data=['推荐数', '成交数', '平均成交价', '总营收'],
        title='各类型镜片推荐接受率对比'
    )
    
    fig.update_layout(
        height=500,
        xaxis_title='镜片类型',
        yaxis_title='接受率(%)',
        xaxis_tickangle=-30,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        title_x=0.5
    )
    
    return fig


def create_myopia_control_chart(control_metrics: pd.DataFrame):
    if control_metrics.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('防控镜片推荐率与接受率', '防控镜片成交占比'),
        specs=[[{'type': 'bar'}, {'type': 'pie'}]]
    )
    
    x_labels = [f"{row['age_group']}-{row['prescription_result']}" 
                for _, row in control_metrics.iterrows()]
    
    fig.add_trace(
        go.Bar(x=x_labels, y=control_metrics['防控镜片推荐率(%)'],
               name='推荐率(%)', marker_color=COLOR_SCHEME['primary']),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=x_labels, y=control_metrics['防控镜片接受率(%)'],
               name='接受率(%)', marker_color=COLOR_SCHEME['success']),
        row=1, col=1
    )
    
    pie_data = control_metrics.groupby('age_group')['防控镜片营收'].sum().reset_index()
    fig.add_trace(
        go.Pie(labels=pie_data['age_group'], values=pie_data['防控镜片营收'],
               name='营收占比'),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        title_text='儿童青少年近视防控接受度分析',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif')
    )
    fig.update_xaxes(tickangle=30, row=1, col=1)
    
    return fig


def create_abnormal_orders_chart(abnormal_df: pd.DataFrame, cleaned_df: pd.DataFrame):
    issues = cleaned_df[cleaned_df['data_quality_issue'] != '']['data_quality_issue'].str.split(';').explode()
    issues = issues[issues != ''].value_counts().reset_index()
    issues.columns = ['问题类型', '数量']
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('异常订单问题类型分布', '各门店异常订单数'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    fig.add_trace(
        go.Bar(x=issues['问题类型'], y=issues['数量'],
               marker_color=COLOR_SCHEME['warning'], name='问题数'),
        row=1, col=1
    )
    
    store_abnormal = cleaned_df[cleaned_df['is_abnormal_order']].groupby('store_name').size().reset_index()
    store_abnormal.columns = ['门店', '异常数']
    
    fig.add_trace(
        go.Bar(x=store_abnormal['门店'], y=store_abnormal['异常数'],
               marker_color=COLOR_SCHEME['warning'], name='异常数'),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        title_text='异常订单分析',
        title_x=0.5,
        showlegend=False,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif')
    )
    fig.update_xaxes(tickangle=30)
    
    return fig


def create_after_sale_correlation_chart(corr_df: pd.DataFrame):
    if corr_df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = px.scatter(
        corr_df,
        x='售后率(%)',
        y='平均客单价',
        size='成交数',
        color='store_name',
        hover_data=['optometrist_name', '返修率(%)', '投诉率(%)', '平均检查项数'],
        title='售后率与客单价关联分析 (气泡大小=成交数)'
    )
    
    fig.update_layout(
        height=550,
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif')
    )
    
    return fig


def create_overall_funnel(funnel_df: pd.DataFrame):
    if funnel_df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    row = funnel_df.iloc[0]
    
    stages = ['验光', '有处方', '推荐', '试戴', '报价', '成交']
    values = [
        row['验光'],
        row['有处方'],
        row['推荐'],
        row['试戴'],
        row['报价'],
        row['成交']
    ]
    
    colors = [COLOR_SCHEME['primary'], COLOR_SCHEME['info'], 
              COLOR_SCHEME['secondary'], COLOR_SCHEME['success'],
              '#bcbd22', COLOR_SCHEME['warning']]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition='inside',
        textinfo='value+percent previous',
        marker=dict(color=colors),
        connector=dict(fillcolor='gray', line=dict(width=0.5))
    ))
    
    fig.update_layout(
        title='整体验光转化漏斗',
        title_x=0.5,
        height=500,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif')
    )
    
    return fig


def create_age_group_chart(age_metrics: pd.DataFrame):
    if age_metrics.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('各年龄段验光数', '各年龄段转化率(%)',
                        '各年龄段总营收(元)', '各年龄段客单价与防控镜片占比'),
        vertical_spacing=0.15
    )
    
    fig.add_trace(
        go.Bar(x=age_metrics['age_group'], y=age_metrics['验光数'],
               marker_color=COLOR_SCHEME['primary'], name='验光数'),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(x=age_metrics['age_group'], y=age_metrics['转化率(%)'],
               marker_color=COLOR_SCHEME['secondary'], name='转化率(%)'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=age_metrics['age_group'], y=age_metrics['总营收'],
               marker_color=COLOR_SCHEME['info'], name='总营收'),
        row=2, col=1
    )
    fig.data[-1].update(xaxis='x3', yaxis='y3')
    
    fig.add_trace(
        go.Bar(x=age_metrics['age_group'], y=age_metrics['客单价'],
               marker_color=COLOR_SCHEME['success'], name='客单价(元)'),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=age_metrics['age_group'], y=age_metrics['防控镜片占比(%)'],
                   mode='lines+markers', marker_color=COLOR_SCHEME['warning'],
                   name='防控镜片占比(%)', yaxis='y4'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=650,
        title_text='年龄段综合分析',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        showlegend=False
    )
    
    return fig


def create_attribution_comparison_chart(attribution_df: pd.DataFrame, summary: dict):
    if attribution_df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('各归因口径成交数对比', '各归因口径转化率对比(%)'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    colors = [COLOR_SCHEME['primary'], COLOR_SCHEME['success'], COLOR_SCHEME['warning'], 
              COLOR_SCHEME['info'], COLOR_SCHEME['secondary']]
    
    fig.add_trace(
        go.Bar(
            x=attribution_df['归因口径'],
            y=attribution_df['成交数'],
            marker_color=colors[:len(attribution_df)],
            text=attribution_df['成交数'],
            textposition='auto',
            name='成交数'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=attribution_df['归因口径'],
            y=attribution_df['转化率(%)'],
            marker_color=colors[:len(attribution_df)],
            text=attribution_df['转化率(%)'].apply(lambda x: f'{x}%'),
            textposition='auto',
            name='转化率(%)'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        title_text='多归因口径对比分析',
        title_x=0.5,
        showlegend=False,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
    )
    
    return fig


def create_store_attribution_chart(store_attr_df: pd.DataFrame):
    if store_attr_df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('各门店不同归因口径成交数', '各门店不同归因口径转化率(%)',
                        '各门店不同归因口径营收(元)', '归因口径对转化率的影响'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    stores = store_attr_df['门店'].tolist()
    
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['门店直接成交数'], name='门店直接', marker_color=COLOR_SCHEME['primary']),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['首次触点成交数'], name='首次触点', marker_color=COLOR_SCHEME['success']),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['末次触点成交数'], name='末次触点', marker_color=COLOR_SCHEME['warning']),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['门店直接转化率(%)'], name='门店直接', marker_color=COLOR_SCHEME['primary']),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['首次触点转化率(%)'], name='首次触点', marker_color=COLOR_SCHEME['success']),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['末次触点转化率(%)'], name='末次触点', marker_color=COLOR_SCHEME['warning']),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['门店直接营收(元)'], name='门店直接', marker_color=COLOR_SCHEME['primary']),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['首次触点营收(元)'], name='首次触点', marker_color=COLOR_SCHEME['success']),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=stores, y=store_attr_df['末次触点营收(元)'], name='末次触点', marker_color=COLOR_SCHEME['warning']),
        row=2, col=1
    )
    
    impact_data = []
    for _, row in store_attr_df.iterrows():
        direct_rate = row['门店直接转化率(%)']
        first_rate = row['首次触点转化率(%)']
        last_rate = row['末次触点转化率(%)']
        impact_data.append({
            '门店': row['门店'],
            '首次触点提升(%)': round(first_rate - direct_rate, 2),
            '末次触点提升(%)': round(last_rate - direct_rate, 2),
        })
    impact_df = pd.DataFrame(impact_data)
    
    fig.add_trace(
        go.Bar(x=impact_df['门店'], y=impact_df['首次触点提升(%)'], name='首次触点提升', marker_color=COLOR_SCHEME['success']),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(x=impact_df['门店'], y=impact_df['末次触点提升(%)'], name='末次触点提升', marker_color=COLOR_SCHEME['warning']),
        row=2, col=2
    )
    
    fig.update_layout(
        height=700,
        title_text='门店多维度归因分析',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5)
    )
    
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(tickangle=30, row=i, col=j)
    
    return fig


def create_cross_store_flow_chart(flow_df: pd.DataFrame):
    if flow_df.empty:
        return go.Figure().update_layout(title='暂无跨店归因数据')
    
    all_stores = sorted(set(flow_df['source'].tolist() + flow_df['target'].tolist()))
    store_to_idx = {store: i for i, store in enumerate(all_stores)}
    
    source_indices = [store_to_idx[s] for s in flow_df['source']]
    target_indices = [store_to_idx[t] for t in flow_df['target']]
    values = flow_df['成交数'].tolist()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    node_colors = [colors[i % len(colors)] for i in range(len(all_stores))]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=all_stores,
            color=node_colors,
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            color='rgba(150, 150, 150, 0.4)',
        )
    )])
    
    fig.update_layout(
        title_text='跨店归因流向图（首次验光门店 → 成交门店）',
        title_x=0.5,
        height=550,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif', size=12),
    )
    
    return fig


def create_channel_distribution_chart(df: pd.DataFrame):
    valid = df[df['is_valid_record']]
    deals = valid[valid['effective_deal']]
    
    if len(deals) == 0:
        return go.Figure().update_layout(title='暂无数据')
    
    channel_stats = deals.groupby('channel').agg(
        成交数=('record_id', 'count'),
        营收=('effective_deal_price', 'sum'),
        顾客数=('customer_id', 'nunique'),
    ).reset_index()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('各渠道成交数分布', '各渠道营收分布'),
        specs=[[{'type': 'pie'}, {'type': 'pie'}]]
    )
    
    fig.add_trace(
        go.Pie(
            labels=channel_stats['channel'],
            values=channel_stats['成交数'],
            name='成交数',
            textinfo='label+percent',
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Pie(
            labels=channel_stats['channel'],
            values=channel_stats['营收'],
            name='营收',
            textinfo='label+percent',
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        title_text='渠道分布分析（门店验光 / 线上补单 / 门店复购）',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
    )
    
    return fig


def create_lens_subtype_overview_chart(lens_df: pd.DataFrame):
    if lens_df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('各镜片类型推荐率与接受率(%)', '各镜片类型退货率与售后率(%)',
                        '各镜片类型总营收(元)', '各镜片类型平均成交价(元)'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    subtypes = lens_df['镜片子类'].tolist()
    
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['推荐率(%)'], name='推荐率(%)', marker_color=COLOR_SCHEME['primary']),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['接受率(%)'], name='接受率(%)', marker_color=COLOR_SCHEME['success']),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['退货率(%)'], name='退货率(%)', marker_color=COLOR_SCHEME['warning']),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['售后率(%)'], name='售后率(%)', marker_color=COLOR_SCHEME['danger'] if 'danger' in COLOR_SCHEME else '#d62728'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['总营收(元)'], name='总营收(元)', marker_color=COLOR_SCHEME['info']),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(x=subtypes, y=lens_df['平均成交价(元)'], name='平均成交价(元)', marker_color=COLOR_SCHEME['secondary']),
        row=2, col=2
    )
    
    fig.update_layout(
        height=650,
        title_text='各类型镜片推荐效果总览',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
    )
    
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(tickangle=30, row=i, col=j)
    
    return fig


def create_lens_effectiveness_by_dimension(df: pd.DataFrame, dimension: str, title: str):
    if df.empty:
        return go.Figure().update_layout(title='暂无数据')
    
    subtypes = sorted(df['lens_subtype'].dropna().unique().tolist())
    dimensions = sorted(df[dimension].dropna().unique().tolist())
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(f'{title} - 推荐接受率(%)', f'{title} - 退货率(%)',
                        f'{title} - 售后率(%)', f'{title} - 平均成交价(元)'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    colors = [COLOR_SCHEME.get('primary', '#1f77b4'), COLOR_SCHEME.get('success', '#2ca02c'),
              COLOR_SCHEME.get('warning', '#ff7f0e'), COLOR_SCHEME.get('info', '#9467bd'),
              COLOR_SCHEME.get('secondary', '#7f7f7f'), COLOR_SCHEME.get('防控', '#e377c2')]
    
    for i, subtype in enumerate(subtypes):
        subtype_data = df[df['lens_subtype'] == subtype]
        color = colors[i % len(colors)]
        
        fig.add_trace(
            go.Bar(x=subtype_data[dimension], y=subtype_data['推荐接受率(%)'],
                   name=subtype, marker_color=color, legendgroup=subtype),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=subtype_data[dimension], y=subtype_data['退货率(%)'],
                   name=subtype, marker_color=color, legendgroup=subtype, showlegend=False),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(x=subtype_data[dimension], y=subtype_data['售后率(%)'],
                   name=subtype, marker_color=color, legendgroup=subtype, showlegend=False),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(x=subtype_data[dimension], y=subtype_data['平均成交价(元)'],
                   name=subtype, marker_color=color, legendgroup=subtype, showlegend=False),
            row=2, col=2
        )
    
    fig.update_layout(
        height=650,
        title_text=f'镜片推荐效果 - {title}分析',
        title_x=0.5,
        font=dict(family='Microsoft YaHei, SimHei, sans-serif'),
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5)
    )
    
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(tickangle=30, row=i, col=j)
    
    return fig


def create_lens_effectiveness_by_age(df: pd.DataFrame):
    age_order = ['0-12岁', '13-18岁', '19-30岁', '31-45岁', '46-60岁', '60岁以上']
    df = df.copy()
    df['age_group'] = pd.Categorical(df['age_group'], categories=age_order, ordered=True)
    df = df.sort_values('age_group')
    return create_lens_effectiveness_by_dimension(df, 'age_group', '按年龄段')


def create_lens_effectiveness_by_prescription(df: pd.DataFrame):
    prescript_order = ['轻度近视', '中度近视', '高度近视', '远视', '散光', '老花', '正常视力']
    df = df.copy()
    available_prescripts = [p for p in prescript_order if p in df['prescription_result'].unique()]
    df['prescription_result'] = pd.Categorical(df['prescription_result'], categories=available_prescripts, ordered=True)
    df = df.sort_values('prescription_result')
    return create_lens_effectiveness_by_dimension(df, 'prescription_result', '按处方类型')


def create_lens_effectiveness_by_price_band(df: pd.DataFrame):
    price_order = ['0-500元', '500-1000元', '1000-2000元', '2000-5000元', '5000元以上']
    df = df.copy()
    available_bands = [b for b in price_order if b in df['price_band'].unique()]
    df['price_band'] = pd.Categorical(df['price_band'], categories=available_bands, ordered=True)
    df = df.sort_values('price_band')
    return create_lens_effectiveness_by_dimension(df, 'price_band', '按价格带')
