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
