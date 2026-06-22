import os
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

from data_generator import generate_all_data
from data_cleaning import clean_data, get_cleaning_summary, get_abnormal_orders
from metrics_calculator import (
    get_overall_metrics, get_conversion_funnel, get_store_metrics,
    get_optometrist_metrics, get_lens_upgrade_rate, get_myopia_control_acceptance,
    get_category_matrix, get_after_sale_correlation, get_age_group_metrics,
    get_all_metric_definitions,
    get_attribution_store_metrics, get_attribution_optometrist_metrics,
    get_cross_store_attribution_flow, get_attribution_conversion_comparison,
    get_lens_subtype_overview, get_lens_effectiveness_by_age,
    get_lens_effectiveness_by_prescription, get_lens_effectiveness_by_price_band,
)
from visualizations import (
    create_store_comparison_chart, create_optometrist_funnel, create_category_matrix,
    create_lens_upgrade_chart, create_myopia_control_chart, create_abnormal_orders_chart,
    create_after_sale_correlation_chart, create_overall_funnel, create_age_group_chart,
    create_attribution_comparison_chart, create_store_attribution_chart,
    create_cross_store_flow_chart, create_channel_distribution_chart,
    create_lens_subtype_overview_chart, create_lens_effectiveness_by_age,
    create_lens_effectiveness_by_prescription, create_lens_effectiveness_by_price_band,
)


def load_or_generate_data():
    os.makedirs('data', exist_ok=True)
    data_file = 'data/optical_records.csv'
    
    if not os.path.exists(data_file):
        print('数据文件不存在，正在生成模拟数据...')
        _, records_df, _, _, _ = generate_all_data()
    else:
        records_df = pd.read_csv(data_file, encoding='utf-8-sig')
    
    cleaned_df = clean_data(records_df)
    return cleaned_df


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

df_raw = load_or_generate_data()

AGE_GROUPS = ['0-12岁', '13-18岁', '19-30岁', '31-45岁', '46-60岁', '60岁以上']
LENS_CATEGORIES = ['基础', '功能', '高端', '防控']
STORES = sorted(df_raw['store_name'].unique().tolist())
PRICE_BANDS = ['0-500元', '500-1000元', '1000-2000元', '2000-5000元', '5000元以上']
LENS_SUBTYPES = sorted([x for x in df_raw['lens_subtype'].dropna().unique().tolist() if x])
PRESCRIPTION_RESULTS = sorted([x for x in df_raw['prescription_result'].dropna().unique().tolist() if x])


def filter_dataframe(df, age_groups, lens_categories, stores):
    filtered = df.copy()
    
    if age_groups and len(age_groups) > 0:
        filtered = filtered[filtered['age_group'].isin(age_groups)]
    
    if lens_categories and len(lens_categories) > 0:
        filtered = filtered[filtered['lens_category'].isin(lens_categories)]
    
    if stores and len(stores) > 0:
        filtered = filtered[filtered['store_name'].isin(stores)]
    
    return filtered


def create_kpi_cards(metrics):
    cards = []
    
    kpi_items = [
        ('验光总数', metrics.get('验光总数', 0), 'primary'),
        ('成交数', metrics.get('成交数', 0), 'success'),
        ('验光成交转化率', metrics.get('验光成交转化率', '0%'), 'info'),
        ('总营收(元)', metrics.get('总营收(元)', 0), 'warning'),
        ('客单价(AOV)', metrics.get('客单价(AOV)', 0), 'secondary'),
    ]
    
    for label, value, color in kpi_items:
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H6(label, className='card-subtitle mb-2 text-muted'),
                        html.H3(f'{value}', className='card-title text-center'),
                    ]),
                    color=color,
                    outline=True,
                    className='shadow-sm'
                ),
                width=2,
                className='mb-3'
            )
        )
    
    return dbc.Row(cards, className='mb-4')


def create_data_quality_cards(summary):
    cards = []
    
    dq_items = [
        ('总记录数', summary.get('总记录数', 0), 'primary'),
        ('有效记录数', summary.get('有效记录数', 0), 'success'),
        ('异常记录数', summary.get('异常记录数', 0), 'danger'),
        ('异常率', summary.get('异常率', '0%'), 'warning'),
        ('多次到店顾客', summary.get('多次到店顾客数', 0), 'info'),
        ('跨店消费顾客', summary.get('跨店消费顾客数', 0), 'secondary'),
    ]
    
    for label, value, color in dq_items:
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H6(label, className='card-subtitle mb-1 text-muted', style={'fontSize': '12px'}),
                        html.H5(f'{value}', className='card-title text-center'),
                    ]),
                    color=color,
                    outline=True,
                    className='shadow-sm'
                ),
                width=2,
                className='mb-2'
            )
        )
    
    return dbc.Row(cards)


app.layout = dbc.Container([
    html.H1('连锁眼镜店验光转化分析系统', 
            className='text-center my-4 text-primary'),
    html.Hr(),
    
    dbc.Card([
        dbc.CardHeader(html.H5('筛选条件')),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('年龄段筛选：', className='font-weight-bold'),
                    dcc.Dropdown(
                        id='age-group-filter',
                        options=[{'label': ag, 'value': ag} for ag in AGE_GROUPS],
                        value=[],
                        multi=True,
                        placeholder='请选择年龄段（不选则全部）'
                    )
                ], width=4),
                dbc.Col([
                    html.Label('镜片品类筛选：', className='font-weight-bold'),
                    dcc.Dropdown(
                        id='lens-category-filter',
                        options=[{'label': lc, 'value': lc} for lc in LENS_CATEGORIES],
                        value=[],
                        multi=True,
                        placeholder='请选择镜片品类（不选则全部）'
                    )
                ], width=4),
                dbc.Col([
                    html.Label('门店筛选：', className='font-weight-bold'),
                    dcc.Dropdown(
                        id='store-filter',
                        options=[{'label': s, 'value': s} for s in STORES],
                        value=[],
                        multi=True,
                        placeholder='请选择门店（不选则全部）'
                    )
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div(id='filter-info', className='mt-2 text-muted')
                ])
            ])
        ])
    ], className='mb-4 shadow'),
    
    dcc.Tabs(id='main-tabs', value='overview', children=[
        dcc.Tab(label='总览看板', value='overview'),
        dcc.Tab(label='门店对比', value='store'),
        dcc.Tab(label='验光师分析', value='optometrist'),
        dcc.Tab(label='品类矩阵', value='category'),
        dcc.Tab(label='防控镜片分析', value='myopia'),
        dcc.Tab(label='归因分析', value='attribution'),
        dcc.Tab(label='镜片推荐效果', value='lens_effect'),
        dcc.Tab(label='异常订单', value='abnormal'),
        dcc.Tab(label='售后关联', value='aftersale'),
        dcc.Tab(label='指标定义', value='definitions'),
    ]),
    
    html.Div(id='tabs-content', className='mt-4'),
    
], fluid=True)


@app.callback(
    Output('tabs-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('age-group-filter', 'value'),
     Input('lens-category-filter', 'value'),
     Input('store-filter', 'value')]
)
def render_content(tab, age_groups, lens_categories, stores):
    df = filter_dataframe(df_raw, age_groups, lens_categories, stores)
    
    if tab == 'overview':
        return render_overview_tab(df)
    elif tab == 'store':
        return render_store_tab(df)
    elif tab == 'optometrist':
        return render_optometrist_tab(df)
    elif tab == 'category':
        return render_category_tab(df)
    elif tab == 'myopia':
        return render_myopia_tab(df)
    elif tab == 'attribution':
        return render_attribution_tab(df)
    elif tab == 'lens_effect':
        return render_lens_effect_tab(df)
    elif tab == 'abnormal':
        return render_abnormal_tab(df)
    elif tab == 'aftersale':
        return render_aftersale_tab(df)
    elif tab == 'definitions':
        return render_definitions_tab()


@app.callback(
    Output('filter-info', 'children'),
    [Input('age-group-filter', 'value'),
     Input('lens-category-filter', 'value'),
     Input('store-filter', 'value')]
)
def update_filter_info(age_groups, lens_categories, stores):
    parts = []
    if age_groups:
        parts.append(f'年龄段: {", ".join(age_groups)}')
    if lens_categories:
        parts.append(f'镜片品类: {", ".join(lens_categories)}')
    if stores:
        parts.append(f'门店: {", ".join(stores)}')
    
    if not parts:
        return '当前：显示全部数据'
    return '当前筛选：' + ' | '.join(parts)


def render_overview_tab(df):
    overall_metrics = get_overall_metrics(df)
    funnel_df = get_conversion_funnel(df)
    summary = get_cleaning_summary(df)
    age_metrics = get_age_group_metrics(df)
    
    return [
        html.H4('核心指标', className='mb-3'),
        create_kpi_cards(overall_metrics),
        
        html.H4('数据质量概览', className='mb-3'),
        create_data_quality_cards(summary),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=create_overall_funnel(funnel_df))
            ], width=6),
            dbc.Col([
                dcc.Graph(figure=create_age_group_chart(age_metrics))
            ], width=6),
        ], className='mb-4'),
        
        html.H4('详细明细数据', className='mb-3'),
        create_detail_table(df),
    ]


def render_store_tab(df):
    store_metrics = get_store_metrics(df)
    
    return [
        html.H4('门店综合对比', className='mb-3'),
        dcc.Graph(figure=create_store_comparison_chart(store_metrics)),
        
        html.H4('门店明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=store_metrics.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in store_metrics.columns],
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('门店明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_optometrist_tab(df):
    opt_metrics = get_optometrist_metrics(df)
    
    return [
        html.H4('验光师转化漏斗对比', className='mb-3'),
        dcc.Graph(figure=create_optometrist_funnel(opt_metrics, top_n=12)),
        
        html.H4('验光师明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=opt_metrics.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in opt_metrics.columns],
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('验光师明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_category_tab(df):
    upgrade_metrics = get_lens_upgrade_rate(df)
    category_matrix = get_category_matrix(df)
    
    return [
        html.H4('镜片品类矩阵（年龄段 × 品类 成交数量）', className='mb-3'),
        dcc.Graph(figure=create_category_matrix(category_matrix)),
        
        html.H4('各类型镜片推荐接受率（镜片升级率）', className='mt-4 mb-3'),
        dcc.Graph(figure=create_lens_upgrade_chart(upgrade_metrics)),
        
        html.H4('镜片品类明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=upgrade_metrics.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in upgrade_metrics.columns],
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('品类明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_myopia_tab(df):
    control_metrics = get_myopia_control_acceptance(df)
    
    return [
        html.H4('儿童青少年近视防控接受度分析', className='mb-3'),
        dcc.Graph(figure=create_myopia_control_chart(control_metrics)),
        
        html.H4('防控镜片明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=control_metrics.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in control_metrics.columns],
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('防控镜片相关明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_abnormal_tab(df):
    abnormal_df = get_abnormal_orders(df)
    
    return [
        html.H4('异常订单分析', className='mb-3'),
        dcc.Graph(figure=create_abnormal_orders_chart(abnormal_df, df)),
        
        html.H4('异常订单明细（前100条）', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=abnormal_df.head(100).to_dict('records'),
            columns=[{'name': col, 'id': col} for col in abnormal_df.columns],
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(255, 200, 200)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(255, 245, 245)'
                }
            ],
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('全部明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_aftersale_tab(df):
    corr_df = get_after_sale_correlation(df)
    
    return [
        html.H4('售后率与客单价关联分析', className='mb-3'),
        dcc.Graph(figure=create_after_sale_correlation_chart(corr_df)),
        
        html.H4('售后关联明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=corr_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in corr_df.columns],
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('售后相关明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_definitions_tab():
    def_df = get_all_metric_definitions()
    
    return [
        html.H4('指标定义说明', className='mb-3'),
        dash_table.DataTable(
            data=def_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in def_df.columns],
            page_size=30,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'left',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif',
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '200px',
                'maxWidth': '500px',
            },
        )
    ]


def render_attribution_tab(df):
    attr_comp_df, attr_summary = get_attribution_conversion_comparison(df)
    store_attr_df = get_attribution_store_metrics(df)
    opt_attr_df = get_attribution_optometrist_metrics(df)
    flow_df = get_cross_store_attribution_flow(df)
    
    summary_cards = [
        ('总验光数', attr_summary.get('总验光数', 0), 'primary'),
        ('总成交数', attr_summary.get('总成交数', 0), 'success'),
        ('跨店成交顾客', attr_summary.get('跨店成交顾客数', 0), 'warning'),
        ('跨店占比(%)', f"{attr_summary.get('跨店成交占比(%)', 0)}%", 'info'),
        ('线上补单顾客', attr_summary.get('线上补单顾客数', 0), 'secondary'),
        ('平均成交周期(天)', attr_summary.get('平均成交周期(天)', 0), 'danger'),
    ]
    
    card_row = dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6(label, className='card-subtitle mb-1 text-muted', style={'fontSize': '12px'}),
                    html.H5(f'{value}', className='card-title text-center'),
                ]),
                color=color,
                outline=True,
                className='shadow-sm'
            ),
            width=2,
            className='mb-3'
        )
        for label, value, color in summary_cards
    ])
    
    return [
        html.H4('归因分析概览', className='mb-3'),
        card_row,
        
        html.H4('多归因口径对比', className='mt-4 mb-3'),
        dcc.Graph(figure=create_attribution_comparison_chart(attr_comp_df, attr_summary)),
        
        dbc.Row([
            dbc.Col([
                html.H4('渠道分布分析', className='mb-3'),
                dcc.Graph(figure=create_channel_distribution_chart(df))
            ], width=6),
            dbc.Col([
                html.H4('跨店归因流向', className='mb-3'),
                dcc.Graph(figure=create_cross_store_flow_chart(flow_df))
            ], width=6),
        ], className='mb-4'),
        
        html.H4('门店多维度归因分析', className='mt-4 mb-3'),
        dcc.Graph(figure=create_store_attribution_chart(store_attr_df)),
        
        html.H4('门店归因明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=store_attr_df.to_dict('records') if not store_attr_df.empty else [],
            columns=[{'name': col, 'id': col} for col in store_attr_df.columns] if not store_attr_df.empty else [],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif',
                'fontSize': '12px'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('验光师归因明细指标', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=opt_attr_df.to_dict('records') if not opt_attr_df.empty else [],
            columns=[{'name': col, 'id': col} for col in opt_attr_df.columns] if not opt_attr_df.empty else [],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif',
                'fontSize': '12px'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('归因相关明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def render_lens_effect_tab(df):
    lens_overview = get_lens_subtype_overview(df)
    lens_by_age = get_lens_effectiveness_by_age(df)
    lens_by_prescript = get_lens_effectiveness_by_prescription(df)
    lens_by_price = get_lens_effectiveness_by_price_band(df)
    
    return [
        html.H4('镜片推荐效果总览', className='mb-3'),
        dcc.Graph(figure=create_lens_subtype_overview_chart(lens_overview)),
        
        html.H4('按年龄段分析', className='mt-4 mb-3'),
        dcc.Graph(figure=create_lens_effectiveness_by_age(lens_by_age)),
        
        html.H4('按处方度数区间分析', className='mt-4 mb-3'),
        dcc.Graph(figure=create_lens_effectiveness_by_prescription(lens_by_prescript)),
        
        html.H4('按价格带分析', className='mt-4 mb-3'),
        dcc.Graph(figure=create_lens_effectiveness_by_price_band(lens_by_price)),
        
        html.H4('镜片推荐效果明细指标（按镜片子类）', className='mt-4 mb-3'),
        dash_table.DataTable(
            data=lens_overview.to_dict('records') if not lens_overview.empty else [],
            columns=[{'name': col, 'id': col} for col in lens_overview.columns] if not lens_overview.empty else [],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'center',
                'fontFamily': 'Microsoft YaHei, SimHei, sans-serif',
                'fontSize': '12px'
            },
            sort_action='native',
            filter_action='native',
        ),
        
        html.H4('推荐效果明细数据', className='mt-4 mb-3'),
        create_detail_table(df),
    ]


def create_detail_table(df, max_rows=200):
    display_cols = [
        'record_id', 'customer_id', 'customer_name', 'age', 'age_group',
        'exam_date', 'store_name', 'optometrist_name', 'channel',
        'exam_items', 'has_prescription', 'prescription_result', 'sphere_degree', 'prescription_degree_band',
        'lens_type_recommended', 'lens_category', 'lens_subtype', 'price_band',
        'tried_on', 'quoted_price', 'deal_made', 'deal_price',
        'is_gift', 'is_return', 'has_after_sale_flag', 'after_sale_type',
        'visit_number', 'is_first_visit', 'is_cross_store',
        'attribution_first_touch_store', 'attribution_last_touch_store',
        'is_abnormal_order', 'data_quality_issue'
    ]
    
    available_cols = [c for c in display_cols if c in df.columns]
    display_df = df[available_cols].head(max_rows).copy()
    
    for col in ['deal_made', 'tried_on', 'has_prescription', 'is_gift', 
                'is_return', 'has_after_sale_flag', 'is_cross_store', 
                'is_abnormal_order', 'is_first_visit', 'is_online_replenish']:
        if col in display_df.columns:
            display_df[col] = display_df[col].map({True: '是', False: '否'})
    
    return dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in display_df.columns],
        page_size=15,
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_cell={
            'textAlign': 'center',
            'fontFamily': 'Microsoft YaHei, SimHei, sans-serif',
            'fontSize': '12px'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{is_abnormal_order} = "是"',
                },
                'backgroundColor': 'rgba(255, 200, 200, 0.5)'
            },
            {
                'if': {
                    'filter_query': '{deal_made} = "是"',
                },
                'backgroundColor': 'rgba(200, 255, 200, 0.3)'
            }
        ],
        sort_action='native',
        filter_action='native',
        export_format='csv',
    )


if __name__ == '__main__':
    print('启动连锁眼镜店验光转化分析系统...')
    print(f'数据加载完成，共 {len(df_raw)} 条记录')
    print('访问地址: http://localhost:8050')
    app.run_server(debug=False, host='0.0.0.0', port=8050)
