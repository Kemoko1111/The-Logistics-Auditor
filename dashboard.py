"""
Veridi Logistics - Delivery Performance Dashboard
Built with Streamlit for interactive exploration of the Olist dataset.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from urllib.request import urlopen

# ─── Page Config ───
st.set_page_config(
    page_title="Veridi Logistics Auditor",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.8;
        font-size: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .metric-card h3 {
        color: #a8a8b3;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    .metric-card .value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.25rem 0;
    }
    .metric-card .sub {
        color: #a8a8b3;
        font-size: 0.8rem;
    }
    
    .green { color: #00d97e; }
    .red { color: #ff6b6b; }
    .blue { color: #6cb4ee; }
    .yellow { color: #ffc107; }
    .purple { color: #b388ff; }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and prepare the master dataset."""
    orders = pd.read_csv('olist_orders_dataset.csv')
    reviews = pd.read_csv('olist_order_reviews_dataset.csv')
    customers = pd.read_csv('olist_customers_dataset.csv')
    products = pd.read_csv('olist_products_dataset.csv')
    order_items = pd.read_csv('olist_order_items_dataset.csv')
    translations = pd.read_csv('product_category_name_translation.csv')

    # Dedup reviews
    reviews_dedup = (reviews
        .sort_values('review_creation_date', ascending=False)
        .drop_duplicates(subset='order_id', keep='first')
    )

    # Join
    master = orders.merge(customers, on='customer_id', how='left')
    master = master.merge(
        reviews_dedup[['order_id', 'review_score']],
        on='order_id', how='left'
    )

    # Dates
    for col in ['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date']:
        master[col] = pd.to_datetime(master[col])

    # Filter delivered
    delivered = master[master['order_status'] == 'delivered'].copy()
    delivered['Days_Difference'] = (
        delivered['order_estimated_delivery_date'] - delivered['order_delivered_customer_date']
    ).dt.days
    delivered = delivered.dropna(subset=['Days_Difference'])

    # Classify
    def classify(d):
        if d >= 0: return 'On Time'
        elif d >= -5: return 'Late'
        else: return 'Super Late'
    delivered['delivery_status'] = delivered['Days_Difference'].apply(classify)

    # Add product categories
    products_en = products.merge(translations, on='product_category_name', how='left')
    products_en['product_category_name_english'] = products_en['product_category_name_english'].fillna('Other')
    items_dedup = order_items.drop_duplicates(subset='order_id', keep='first')
    delivered = delivered.merge(
        items_dedup[['order_id', 'product_id']], on='order_id', how='left'
    ).merge(
        products_en[['product_id', 'product_category_name_english']], on='product_id', how='left'
    )
    delivered['product_category_name_english'] = delivered['product_category_name_english'].fillna('Unknown')

    # Add purchase month
    delivered['purchase_month'] = delivered['order_purchase_timestamp'].dt.to_period('M').astype(str)

    return delivered


@st.cache_data
def load_geojson():
    """Load Brazil states GeoJSON."""
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    with urlopen(url) as response:
        geo = json.loads(response.read())
    for feature in geo['features']:
        feature['id'] = feature['properties']['sigla']
    return geo


# ─── Load Data ───
delivered = load_data()
brazil_geo = load_geojson()

# ─── Sidebar Filters ───
st.sidebar.markdown("## 🔍 Filters")

states = sorted(delivered['customer_state'].unique())
selected_states = st.sidebar.multiselect("States", states, default=states)

statuses = ['On Time', 'Late', 'Super Late']
selected_statuses = st.sidebar.multiselect("Delivery Status", statuses, default=statuses)

categories = sorted(delivered['product_category_name_english'].unique())
selected_categories = st.sidebar.multiselect(
    "Product Categories (top 20)",
    delivered['product_category_name_english'].value_counts().head(20).index.tolist(),
    default=delivered['product_category_name_english'].value_counts().head(20).index.tolist()
)

# Apply filters
df = delivered[
    (delivered['customer_state'].isin(selected_states)) &
    (delivered['delivery_status'].isin(selected_statuses)) &
    (delivered['product_category_name_english'].isin(selected_categories))
]

# ─── Header ───
st.markdown("""
<div class="main-header">
    <h1>🚚 Veridi Logistics — Delivery Performance Auditor</h1>
    <p>Connecting delivery timeliness with customer sentiment across Brazilian states</p>
</div>
""", unsafe_allow_html=True)

# ─── KPI Cards ───
total = len(df)
on_time = (df['delivery_status'] == 'On Time').sum()
late = (df['delivery_status'].isin(['Late', 'Super Late'])).sum()
avg_delay = df['Days_Difference'].mean() if total else 0
avg_review = df['review_score'].mean() if total else 0

# Safe fallbacks for NaN
import math
if math.isnan(avg_delay): avg_delay = 0.0
if math.isnan(avg_review): avg_review = 0.0

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""<div class="metric-card">
        <h3>Total Orders</h3>
        <div class="value blue">{total:,}</div>
        <div class="sub">Filtered results</div>
    </div>""", unsafe_allow_html=True)

with c2:
    pct_on = on_time / total * 100 if total else 0
    st.markdown(f"""<div class="metric-card">
        <h3>On Time</h3>
        <div class="value green">{pct_on:.1f}%</div>
        <div class="sub">{on_time:,} orders</div>
    </div>""", unsafe_allow_html=True)

with c3:
    pct_late = late / total * 100 if total else 0
    st.markdown(f"""<div class="metric-card">
        <h3>Late / Super Late</h3>
        <div class="value red">{pct_late:.1f}%</div>
        <div class="sub">{late:,} orders</div>
    </div>""", unsafe_allow_html=True)

with c4:
    delay_color = 'green' if avg_delay >= 0 else 'red'
    st.markdown(f"""<div class="metric-card">
        <h3>Avg Days Early</h3>
        <div class="value {delay_color}">{avg_delay:+.1f}</div>
        <div class="sub">Estimated − Actual</div>
    </div>""", unsafe_allow_html=True)

with c5:
    stars = '★' * int(round(avg_review)) if avg_review > 0 else '☆'
    st.markdown(f"""<div class="metric-card">
        <h3>Avg Review Score</h3>
        <div class="value yellow">{stars} {avg_review:.2f}</div>
        <div class="sub">Out of 5.0</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── Empty data guard ───
if total == 0:
    st.warning("No data matches the current filters. Please select at least one State, Delivery Status, and Product Category.")
    st.stop()

# ─── Row 1: Map + State Bar Chart ───
st.markdown('<div class="section-title">📍 Geographic Analysis — Late Deliveries by State</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

state_stats = df.groupby('customer_state').agg(
    total_orders=('order_id', 'count'),
    late_orders=('delivery_status', lambda x: x.isin(['Late', 'Super Late']).sum()),
    avg_delay=('Days_Difference', 'mean'),
    avg_review=('review_score', 'mean')
).reset_index()
state_stats['pct_late'] = (state_stats['late_orders'] / state_stats['total_orders'] * 100).round(1)
state_stats = state_stats.sort_values('pct_late', ascending=False)

brazil_names = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapa', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceara', 'DF': 'Distrito Federal', 'ES': 'Espirito Santo',
    'GO': 'Goias', 'MA': 'Maranhao', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Para', 'PB': 'Paraiba', 'PR': 'Parana',
    'PE': 'Pernambuco', 'PI': 'Piaui', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondonia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'Sao Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}
state_stats['state_name'] = state_stats['customer_state'].map(brazil_names)

with col1:
    fig_map = px.choropleth(
        state_stats,
        locations='customer_state',
        geojson=brazil_geo,
        color='pct_late',
        color_continuous_scale='RdYlGn_r',
        labels={'pct_late': '% Late', 'customer_state': 'State'},
        hover_name='state_name',
        hover_data={'total_orders': True, 'pct_late': ':.1f'}
    )
    fig_map.update_geos(fitbounds='locations', visible=False)
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar=dict(title="% Late")
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    fig_bar = px.bar(
        state_stats.head(15),
        x='pct_late', y='customer_state',
        orientation='h',
        color='pct_late',
        color_continuous_scale='RdYlGn_r',
        labels={'pct_late': '% Late', 'customer_state': 'State'},
        hover_data={'state_name': True, 'total_orders': True}
    )
    fig_bar.update_layout(
        yaxis=dict(autorange='reversed'),
        height=450,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ─── Row 2: Sentiment Analysis ───
st.markdown('<div class="section-title">💬 Sentiment Correlation — Do Late Deliveries Cause Bad Reviews?</div>', unsafe_allow_html=True)

col3, col4 = st.columns([1, 1])

with col3:
    sentiment = df.groupby('delivery_status')['review_score'].mean().reindex(['On Time', 'Late', 'Super Late'])
    fig_sent = go.Figure(data=[
        go.Bar(
            x=sentiment.index,
            y=sentiment.values,
            marker_color=['#00d97e', '#ffc107', '#ff6b6b'],
            text=[f'{v:.2f}' for v in sentiment.values],
            textposition='outside',
            textfont=dict(size=14, color='white')
        )
    ])
    fig_sent.update_layout(
        title="Average Review Score by Delivery Status",
        yaxis=dict(range=[0, 5.5], title="Avg Review Score"),
        xaxis=dict(title=""),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    st.plotly_chart(fig_sent, use_container_width=True)

with col4:
    delay_bins = df.copy()
    delay_bins['delay_bin'] = pd.cut(
        delay_bins['Days_Difference'],
        bins=[-100, -20, -10, -5, 0, 5, 10, 20, 50, 100],
        labels=['>20d late', '10-20d late', '5-10d late', '1-5d late',
                '0-5d early', '5-10d early', '10-20d early', '20-50d early', '50+d early']
    )
    binned = delay_bins.groupby('delay_bin', observed=True)['review_score'].mean().reset_index()

    fig_delay = px.bar(
        binned, x='delay_bin', y='review_score',
        color='review_score',
        color_continuous_scale='RdYlGn',
        labels={'delay_bin': 'Delivery Timing', 'review_score': 'Avg Review'}
    )
    fig_delay.update_layout(
        title="The Later the Delivery, the Worse the Review",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(tickangle=45),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_delay, use_container_width=True)

st.markdown("---")

# ─── Row 3: Category Analysis ───
st.markdown('<div class="section-title">📦 Product Category Analysis — Which Categories Struggle Most?</div>', unsafe_allow_html=True)

top_cats = df['product_category_name_english'].value_counts().head(15).index
cat_stats = df[df['product_category_name_english'].isin(top_cats)].groupby(
    'product_category_name_english'
).agg(
    total_orders=('order_id', 'count'),
    pct_late=('delivery_status', lambda x: x.isin(['Late', 'Super Late']).mean() * 100),
    avg_review=('review_score', 'mean')
).round(2).sort_values('pct_late', ascending=False)

col5, col6 = st.columns([1, 1])

with col5:
    fig_cat = px.bar(
        cat_stats.reset_index(),
        x='pct_late', y='product_category_name_english',
        orientation='h',
        color='pct_late',
        color_continuous_scale='RdYlGn_r',
        labels={'pct_late': '% Late', 'product_category_name_english': 'Category'}
    )
    fig_cat.update_layout(
        title="Late Delivery Rate by Category",
        yaxis=dict(autorange='reversed'),
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col6:
    fig_rev = px.bar(
        cat_stats.sort_values('avg_review').reset_index(),
        x='avg_review', y='product_category_name_english',
        orientation='h',
        color='avg_review',
        color_continuous_scale='RdYlGn',
        labels={'avg_review': 'Avg Review', 'product_category_name_english': 'Category'}
    )
    fig_rev.update_layout(
        title="Average Review Score by Category",
        yaxis=dict(autorange='reversed'),
        height=500,
        xaxis=dict(range=[0, 5.5]),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_rev, use_container_width=True)

st.markdown("---")

# ─── Row 4: Monthly Trend ───
st.markdown('<div class="section-title">📈 Monthly Trend — Late Delivery Rate Over Time</div>', unsafe_allow_html=True)

monthly = df.groupby('purchase_month').agg(
    total=('order_id', 'count'),
    late=('delivery_status', lambda x: x.isin(['Late', 'Super Late']).sum())
).reset_index()
monthly['pct_late'] = (monthly['late'] / monthly['total'] * 100).round(1)
monthly = monthly[monthly['total'] >= 50]  # filter months with too few orders

fig_trend = px.line(
    monthly, x='purchase_month', y='pct_late',
    markers=True,
    labels={'purchase_month': 'Month', 'pct_late': '% Late Deliveries'}
)
fig_trend.update_layout(
    height=350,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    xaxis=dict(tickangle=45)
)
fig_trend.update_traces(line_color='#6cb4ee', marker_color='#ff6b6b')
st.plotly_chart(fig_trend, use_container_width=True)

# ─── Footer ───
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a8a8b3; font-size: 0.85rem; padding: 1rem;">
    <strong>Veridi Logistics Auditor</strong> · Built with Streamlit · Data: Olist Brazilian E-Commerce Dataset<br>
    Analysis by The Last Mile Logistics Audit Team
</div>
""", unsafe_allow_html=True)
