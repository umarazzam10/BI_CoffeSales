import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import numpy as np

# Custom CSS untuk styling
def load_css():
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
            color: white;
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        
        .main-header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #8B4513;
        }
        
        .status-info {
            background: linear-gradient(135deg, #E6F3FF 0%, #CCE7FF 100%);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .prediction-card {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            margin: 0.5rem;
        }
        
        .stMetric {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .trending-item {
            text-align: center; 
            padding: 1rem; 
            background: white; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .trending-emoji {
            font-size: 2rem;
        }
        
        .trending-name {
            font-weight: bold; 
            margin: 0.5rem 0;
        }
        
        .trending-count {
            color: #8B4513; 
            font-weight: bold;
        }
        
        .filter-info {
            background: #f0f8ff;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #4CAF50;
        }
    </style>
    """, unsafe_allow_html=True)

# Fungsi untuk membuat koneksi database
@st.cache_resource
def create_connection():
    try:
        # Format: mysql+pymysql://username:password@host:port/database
        DATABASE_URL = "mysql+pymysql://root:@localhost:3306/coffeedw"
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Test koneksi
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        return engine
    except Exception as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Fungsi untuk mengambil data dari database
@st.cache_data(ttl=300)  # Cache selama 5 menit
def fetch_data():
    engine = create_connection()
    if engine is None:
        return None
    
    try:
        # Query untuk mengambil data dari fact_sales dengan join
        query = """
        SELECT
            fs.transaction_id,
            fs.transaction_qty,
            fs.unit_price,
            fs.total_bill,
            dt.transaction_date,
            dt.transaction_time,
            dt.year,
            dt.month,
            dt.month_name,
            dt.day,
            dt.day_name,
            dt.day_of_week,
            dt.hour,
            dp.product_category,
            dp.product_type,
            dp.product_detail,
            dp.size,
            ds.store_location
        FROM fact_sales fs
        JOIN dim_time dt ON fs.time_id = dt.time_id
        JOIN dim_product dp ON fs.product_id = dp.product_id
        JOIN dim_store ds ON fs.store_id = ds.store_id
        ORDER BY dt.transaction_date DESC
        """
        
        # Menggunakan pandas.read_sql dengan SQLAlchemy engine
        df = pd.read_sql(query, engine)
        
        # Konversi tanggal dan pastikan format yang benar
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['month_year'] = df['transaction_date'].dt.to_period('M')
        
        # Pastikan kolom year dan month adalah integer
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        df['month'] = pd.to_numeric(df['month'], errors='coerce').astype('Int64')
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fungsi untuk filter data berdasarkan periode (DIPERBAIKI)
def filter_data_by_period(df, selected_year, selected_month=None):
    if df is None or df.empty:
        return df, df
    
    df_filtered = df.copy()
    df_previous = pd.DataFrame()
    
    # Filter berdasarkan tahun
    if selected_year != "All Time":
        year_int = int(selected_year)
        df_filtered = df_filtered[df_filtered['year'] == year_int]
        
        # Filter berdasarkan bulan jika dipilih
        if selected_month and selected_month != "All Months":
            # Mapping nama bulan ke angka
            month_mapping = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12
            }
            
            month_num = month_mapping.get(selected_month)
            if month_num:
                df_filtered = df_filtered[df_filtered['month'] == month_num]
                
                # Data bulan sebelumnya untuk growth calculation
                if month_num == 1:
                    prev_year = year_int - 1
                    prev_month = 12
                else:
                    prev_year = year_int
                    prev_month = month_num - 1
                    
                df_previous = df[(df['year'] == prev_year) & (df['month'] == prev_month)]
        else:
            # Data tahun sebelumnya untuk growth calculation
            prev_year = year_int - 1
            df_previous = df[df['year'] == prev_year]
    else:
        # Untuk All Time, tidak ada data previous untuk comparison
        df_filtered = df
        df_previous = pd.DataFrame()
    
    return df_filtered, df_previous

# Fungsi untuk menghitung KPI (DIPERBAIKI)
def calculate_kpis(df_current, df_previous, show_growth=True):
    if df_current is None or df_current.empty:
        return {
            'total_revenue': 0,
            'top_menu': "N/A",
            'peak_time': "08:30",
            'best_branch': "N/A",
            'total_customers': 0,
            'revenue_growth': 0 if show_growth else None,
            'menu_growth': 0 if show_growth else None,
            'customer_growth': 0 if show_growth else None,
            'branch_performance': 0 if show_growth else None
        }
    
    # Total Revenue
    total_revenue = df_current['total_bill'].sum()
    
    # Menu yang paling banyak dibeli
    if not df_current.empty:
        top_menu_data = df_current.groupby('product_detail')['transaction_qty'].sum()
        if not top_menu_data.empty:
            top_menu = top_menu_data.idxmax()
            top_menu_qty = top_menu_data.max()
        else:
            top_menu = "N/A"
            top_menu_qty = 0
    else:
        top_menu = "N/A"
        top_menu_qty = 0
    
    # Peak Time (jam dengan transaksi terbanyak)
    if 'hour' in df_current.columns and not df_current['hour'].isna().all():
        hour_data = df_current.dropna(subset=['hour'])
        if not hour_data.empty:
            peak_hour = hour_data.groupby('hour')['transaction_qty'].sum().idxmax()
            peak_time = f"{int(peak_hour):02d}:30"
        else:
            peak_time = "08:30"
    else:
        peak_time = "08:30"
    
    # Total Customers (unique transactions)
    total_customers = df_current['transaction_id'].nunique()
    
    # Best Branch
    if not df_current.empty:
        branch_performance = df_current.groupby('store_location')['total_bill'].sum()
        if not branch_performance.empty:
            best_branch = branch_performance.idxmax()
        else:
            best_branch = "N/A"
    else:
        best_branch = "N/A"
    
    # Growth calculations
    revenue_growth = None
    menu_growth = None
    customer_growth = None
    
    if show_growth and not df_previous.empty:
        # Revenue Growth
        prev_revenue = df_previous['total_bill'].sum()
        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        # Menu Growth (berdasarkan top menu saat ini)
        if top_menu != "N/A":
            prev_menu_qty = df_previous[df_previous['product_detail'] == top_menu]['transaction_qty'].sum()
            if prev_menu_qty > 0:
                menu_growth = ((top_menu_qty - prev_menu_qty) / prev_menu_qty) * 100
        
        # Customer Growth
        prev_customers = df_previous['transaction_id'].nunique()
        if prev_customers > 0:
            customer_growth = ((total_customers - prev_customers) / prev_customers) * 100
    
    return {
        'total_revenue': total_revenue,
        'top_menu': top_menu,
        'top_menu_qty': top_menu_qty,
        'peak_time': peak_time,
        'best_branch': best_branch,
        'total_customers': total_customers,
        'revenue_growth': revenue_growth,
        'menu_growth': menu_growth,
        'customer_growth': customer_growth,
    }

# Fungsi untuk membuat filter sidebar (DIPERBAIKI)
def create_filters(df):
    st.sidebar.markdown("## 🔍 Filter Data")
    
    # Filter Tahun
    if df is not None and not df.empty:
        # Ambil tahun unik dan pastikan dalam format yang benar
        available_years = sorted([int(year) for year in df['year'].dropna().unique()])
        year_options = ["All Time"] + [str(year) for year in available_years]
    else:
        year_options = ["All Time"]
    
    selected_year = st.sidebar.selectbox(
        "📅 Pilih Tahun:",
        options=year_options,
        index=0
    )
    
    # Filter Bulan (hanya tampil jika bukan All Time)
    selected_month = None
    if selected_year != "All Time":
        month_options = ["All Months"] + [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        selected_month = st.sidebar.selectbox(
            "📅 Pilih Bulan:",
            options=month_options,
            index=0
        )
    
    # Tampilkan info filter yang aktif
    if selected_year != "All Time":
        filter_text = f"Tahun: {selected_year}"
        if selected_month and selected_month != "All Months":
            filter_text += f", Bulan: {selected_month}"
        
        st.sidebar.markdown(f"""
        <div style="background: #e8f5e8; padding: 0.5rem; border-radius: 5px; margin-top: 1rem;">
            <small><strong>Filter Aktif:</strong><br>{filter_text}</small>
        </div>
        """, unsafe_allow_html=True)
    
    return selected_year, selected_month

# Fungsi untuk membuat chart trend penjualan (DIPERBAIKI)
def create_sales_trend_chart(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Trend Penjualan Coffee Shop", height=400)
        return fig
    
    # Aggregate data by month-year
    df_chart = df.copy()
    df_chart['month_year_str'] = df_chart['transaction_date'].dt.strftime('%Y-%m')
    
    monthly_data = df_chart.groupby('month_year_str').agg({
        'total_bill': 'sum',
        'transaction_id': 'nunique'
    }).reset_index()
    
    # Sort by month_year_str
    monthly_data = monthly_data.sort_values('month_year_str')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Revenue line
    fig.add_trace(
        go.Scatter(
            x=monthly_data['month_year_str'],
            y=monthly_data['total_bill'],
            name="Revenue (Dollar)",
            line=dict(color='#8B4513', width=3),
            mode='lines+markers'
        ),
        secondary_y=False,
    )
    
    # Customers line
    fig.add_trace(
        go.Scatter(
            x=monthly_data['month_year_str'],
            y=monthly_data['transaction_id'],
            name="Total Customers",
            line=dict(color='#D2691E', width=2, dash='dash'),
            mode='lines+markers'
        ),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text="Periode")
    fig.update_yaxes(title_text="Revenue (Dolar)", secondary_y=False)
    fig.update_yaxes(title_text="Total Customers", secondary_y=True)
    
    fig.update_layout(
        title="Trend Penjualan Coffee Shop",
        height=400,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Fungsi untuk membuat chart menu performance
def create_menu_performance_chart(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Top Menu Items Performance", height=400)
        return fig
    
    # Top menu items
    menu_performance = df.groupby('product_detail').agg({
        'transaction_qty': 'sum',
        'total_bill': 'sum'
    }).reset_index().sort_values('total_bill', ascending=False).head(10)
    
    # Create donut chart
    fig = go.Figure(data=[go.Pie(
        labels=menu_performance['product_detail'],
        values=menu_performance['total_bill'],
        hole=.6,
        marker_colors=px.colors.qualitative.Set3
    )])
    
    fig.update_layout(
        title="Top Menu Items Performance",
        height=400,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Fungsi untuk membuat chart revenue by category
def create_revenue_category_chart(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Revenue by Category", height=300)
        return fig
    
    category_revenue = df.groupby('product_category')['total_bill'].sum().reset_index()
    category_revenue = category_revenue.sort_values('total_bill', ascending=True)
    
    fig = go.Figure(data=[go.Bar(
        x=category_revenue['total_bill'],
        y=category_revenue['product_category'],
        orientation='h',
        marker_color='#8B4513'
    )])
    
    fig.update_layout(
        title="Revenue by Category",
        height=300,
        xaxis_title="Revenue (Dolar)",
        yaxis_title="Category",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Fungsi untuk membuat chart peak hours
def create_peak_hours_chart(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Peak Hours Analysis - Customer Traffic", height=300)
        return fig
    
    # Filter data yang memiliki nilai hour
    df_hours = df.dropna(subset=['hour'])
    if df_hours.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data jam untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Peak Hours Analysis - Customer Traffic", height=300)
        return fig
    
    hourly_data = df_hours.groupby('hour')['transaction_qty'].sum().reset_index()
    
    fig = go.Figure(data=[go.Bar(
        x=hourly_data['hour'],
        y=hourly_data['transaction_qty'],
        marker_color=['#CD853F' if x in [8, 9, 10, 11, 12, 13, 14, 15] else '#8B4513' for x in hourly_data['hour']],
        text=hourly_data['transaction_qty'],
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Peak Hours Analysis - Customer Traffic",
        height=300,
        xaxis_title="Jam",
        yaxis_title="Jumlah Customer",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Fungsi untuk membuat branch performance chart
def create_branch_performance_chart(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk ditampilkan", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Branch Performance Comparison", height=300)
        return fig
    
    branch_data = df.groupby('store_location')['total_bill'].sum().reset_index()
    
    # Radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=branch_data['total_bill'],
        theta=branch_data['store_location'],
        fill='toself',
        name='Revenue (Dolar)',
        line_color='#8B4513'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, (branch_data['total_bill'].max()) * 1.1] if not branch_data.empty else [0, 1]
            )),
        title="Branch Performance Comparison",
        height=300
    )
    
    return fig

# Fungsi utama dashboard
def display_dashboard():
    # Load CSS
    load_css()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>☕ Coffee Analytics Dashboard</h1>
        <p>Real-time Business Intelligence untuk Coffee Shop Modern</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner('Memuat data dari database...'):
        df = fetch_data()
    
    if df is None:
        st.error("❌ Tidak dapat memuat data dari database. Pastikan:")
        st.error("1. Database MySQL sudah berjalan")
        st.error("2. Database 'coffeedw' sudah dibuat")
        st.error("3. Tabel sudah terisi dengan data melalui proses ETL")
        st.info("💡 Silakan upload data melalui halaman ETL terlebih dahulu")
        return
    
    if df.empty:
        st.warning("⚠️ Database tersedia tetapi belum ada data. Silakan upload data melalui halaman ETL.")
        return
    
    # Create filters
    selected_year, selected_month = create_filters(df)
    
    # Filter data
    df_filtered, df_previous = filter_data_by_period(df, selected_year, selected_month)
    
    # Status info dengan informasi filter
    current_time = datetime.datetime.now()
    period_text = f"Periode: {selected_year}"
    if selected_month and selected_month != "All Months":
        period_text += f" - {selected_month}"
    
    # Tampilkan info jumlah data yang difilter
    total_records = len(df_filtered) if df_filtered is not None else 0
    total_all_records = len(df) if df is not None else 0
    
    st.markdown(f"""
    <div class="status-info">
        <p>🕐 {current_time.strftime('%A, %d %B %Y - %H:%M:%S')} | 
        📊 {period_text} | 📈 {total_records:,} dari {total_all_records:,} records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan info jika tidak ada data setelah filter
    if df_filtered is None or df_filtered.empty:
        st.warning(f"⚠️ Tidak ada data untuk periode yang dipilih: {period_text}")
        st.info("💡 Coba pilih periode yang berbeda atau gunakan 'All Time'")
        return
    
    # Calculate KPIs
    show_growth = selected_year != "All Time"
    kpis = calculate_kpis(df_filtered, df_previous, show_growth)
    
    # KPI Section
    st.markdown("## 📊 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        delta_text = f"{kpis['revenue_growth']:.1f}%" if kpis['revenue_growth'] is not None else None
        st.metric(
            label="Sales Revenue",
            value=f"${kpis['total_revenue']:,.0f}",
            delta=delta_text
        )
    
    with col2:
        delta_text = f"{kpis['menu_growth']:.1f}%" if kpis['menu_growth'] is not None else None
        st.metric(
            label="Top Menu",
            value=kpis['top_menu'][:15] + "..." if len(kpis['top_menu']) > 15 else kpis['top_menu'],
            delta=delta_text,
            help=f"Penjualan: {kpis.get('top_menu_qty', 0)} cups"
        )
    
    with col3:
        st.metric(
            label="Peak Time",
            value=kpis['peak_time'],
        )
    
    with col4:
        st.metric(
            label="Best Branch",
            value=kpis['best_branch'],
        )
    
    with col5:
        delta_text = f"{kpis['customer_growth']:.1f}%" if kpis['customer_growth'] is not None else None
        st.metric(
            label="Total Customer",
            value=f"{kpis['total_customers']}",
            delta=delta_text
        )
    
    # Analytics Dashboard Section
    st.markdown("## 📈 Analytics Dashboard")
    
    # Row 1: Sales Trend and Menu Performance
    col1, col2 = st.columns([2, 1])
    
    with col1:
        trend_chart = create_sales_trend_chart(df_filtered)
        st.plotly_chart(trend_chart, use_container_width=True)
    
    with col2:
        menu_chart = create_menu_performance_chart(df_filtered)
        st.plotly_chart(menu_chart, use_container_width=True)
    
    # Row 2: Revenue by Category, Branch Performance, Peak Hours
    col1, col2, col3 = st.columns(3)
    
    with col1:
        revenue_chart = create_revenue_category_chart(df_filtered)
        st.plotly_chart(revenue_chart, use_container_width=True)
    
    with col2:
        branch_chart = create_branch_performance_chart(df_filtered)
        st.plotly_chart(branch_chart, use_container_width=True)
    
    with col3:
        peak_chart = create_peak_hours_chart(df_filtered)
        st.plotly_chart(peak_chart, use_container_width=True)
    
    # Trending Menu Items
    st.markdown("## 🔥 Trending Menu Items")
    
    if df_filtered is not None and not df_filtered.empty:
        trending_items = df_filtered.groupby('product_detail').agg({
            'transaction_qty': 'sum',
            'total_bill': 'sum'
        }).reset_index().sort_values('transaction_qty', ascending=False).head(6)
        
        if not trending_items.empty:
            cols = st.columns(6)
            
            # Emoji mapping untuk produk
            product_emojis = {
                'Es Kopi Susu': '☕',
                'Brown Sugar Latte': '🥛',
                'Cheesecake': '🍰',
                'Club Sandwich': '🥪',
                'Matcha Latte': '🍵',
                'Caesar Salad': '🥗',
                'Americano': '☕',
                'Cappuccino': '☕',
                'Croissant': '🥐',
                'Lemon Tea': '🍋'
            }
            
            for idx, (_, item) in enumerate(trending_items.iterrows()):
                if idx < 6:
                    with cols[idx]:
                        emoji = product_emojis.get(item['product_detail'], '☕')
                        st.markdown(f"""
                        <div class="trending-item">
                            <div class="trending-emoji">{emoji}</div>
                            <div class="trending-name">{item['product_detail']}</div>
                            <div class="trending-count">{item['transaction_qty']} cup</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Prediction Section
    st.markdown("## 🔮 Prediction")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.selectbox("Jenis Prediksi", ["Prediksi Penjualan"], key="pred_type")
        st.selectbox("Periode", ["3 hari kedepan"], key="pred_period")
        
        if st.button("🎯 Generate Prediksi", type="primary"):
            st.success("Prediksi berhasil di-generate!")
    
    with col2:
        col2_1, col2_2, col2_3, col2_4 = st.columns(4)
        
        with col2_1:
            st.markdown("""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Prediksi 3 Hari</div>
                <div style="font-size: 1.8rem; font-weight: bold;">$60K</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2_2:
            st.markdown("""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Confidence</div>
                <div style="font-size: 1.8rem; font-weight: bold;">89.6%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2_3:
            st.markdown("""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">⚠️ Risk Level</div>
                <div style="font-size: 1.5rem; font-weight: bold;">17.0%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2_4:
            st.markdown("""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">📊 Trend</div>
                <div style="font-size: 1.5rem; font-weight: bold;">STABLE</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 Total Records: {:,}".format(len(df_filtered)))
    
    with col2:
        if not df_filtered.empty:
            st.info("📅 Data Range: {} - {}".format(
                df_filtered['transaction_date'].min().strftime('%Y-%m-%d'),
                df_filtered['transaction_date'].max().strftime('%Y-%m-%d')
            ))
        else:
            st.info("📅 No data available")
    
    with col3:
        st.info("🔄 Last Update: {}".format(datetime.datetime.now().strftime('%H:%M:%S')))

# Fungsi untuk refresh data
def refresh_data():
    st.cache_data.clear()
    st.rerun()