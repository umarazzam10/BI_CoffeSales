import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
from prophet.diagnostics import cross_validation, performance_metrics
import warnings
warnings.filterwarnings('ignore')

# Custom CSS untuk styling prediction
def load_prediction_css():
    st.markdown("""
    <style>
        .prediction-header {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
            color: white;
        }
        
        .prediction-card {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            margin: 0.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .model-performance {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #8B4513;
            margin: 1rem 0;
        }
        
        .prediction-insight {
            background: linear-gradient(135deg, #E6F3FF 0%, #CCE7FF 100%);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #4CAF50;
        }
        
        .warning-card {
            background: linear-gradient(135deg, #FFE6E6 0%, #FFCCCC 100%);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #FF6B6B;
        }
        
        .prophet-info {
            background: linear-gradient(135deg, #F0F8FF 0%, #E0F0FF 100%);
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #0066CC;
        }
    </style>
    """, unsafe_allow_html=True)

# Fungsi untuk membuat koneksi database
@st.cache_resource
def create_connection():
    try:
        DATABASE_URL = "mysql+pymysql://root:@localhost:3306/coffeedw"
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        return engine
    except Exception as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Fungsi untuk mengambil data untuk prediksi
@st.cache_data(ttl=300)
def fetch_prediction_data():
    engine = create_connection()
    if engine is None:
        return None
    
    try:
        query = """
        SELECT
            fs.transaction_id,
            fs.transaction_qty,
            fs.unit_price,
            fs.total_bill,
            dt.transaction_date,
            dt.year,
            dt.month,
            dt.day,
            dt.day_of_week,
            dt.hour,
            dp.product_category,
            dp.product_type,
            ds.store_location
        FROM fact_sales fs
        JOIN dim_time dt ON fs.time_id = dt.time_id
        JOIN dim_product dp ON fs.product_id = dp.product_id
        JOIN dim_store ds ON fs.store_id = ds.store_id
        ORDER BY dt.transaction_date DESC
        """
        
        df = pd.read_sql(query, engine)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching prediction data: {e}")
        return None

# Fungsi untuk mempersiapkan data untuk Prophet
def prepare_prophet_data(df):
    """
    Mempersiapkan data untuk Facebook Prophet
    Prophet membutuhkan format data dengan kolom 'ds' (tanggal) dan 'y' (nilai target)
    """
    if df is None or df.empty:
        return None, None
    
    # Aggregate data harian
    daily_data = df.groupby('transaction_date').agg({
        'total_bill': 'sum',
        'transaction_qty': 'sum',
        'transaction_id': 'nunique'
    }).reset_index()
    
    daily_data.columns = ['ds', 'y', 'quantity', 'customers']
    daily_data = daily_data.sort_values('ds')
    
    # Prophet membutuhkan minimal 2 data point
    if len(daily_data) < 2:
        return None, None
    
    # Format data untuk Prophet (hanya perlu 'ds' dan 'y')
    prophet_data = daily_data[['ds', 'y']].copy()
    
    return prophet_data, daily_data

# Fungsi untuk membuat dan melatih model Prophet
def train_prophet_model(prophet_data, seasonality_mode='additive'):
    if prophet_data is None or prophet_data.empty:
        return None, None
    
    try:
        # Inisialisasi model Prophet tanpa parameter verbose
        model = Prophet(
            growth='linear',
            seasonality_mode=seasonality_mode,
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_prior_scale=10.0,
            holidays_prior_scale=10.0,
            changepoint_prior_scale=0.05,
            interval_width=0.80
            # HAPUS verbose=False
        )
        
        # Suppress logging
        import logging
        logging.getLogger('prophet').setLevel(logging.WARNING)
        
        model.add_seasonality(name='weekend', period=7, fourier_order=3)
        model.fit(prophet_data)
        
        future = model.make_future_dataframe(periods=0)
        forecast = model.predict(future)
        
        return model, forecast
        
    except Exception as e:
        st.error(f"Error training Prophet model: {e}")
        return None, None
# Fungsi untuk membuat prediksi masa depan
def make_prophet_predictions(model, periods=7):
    """
    Membuat prediksi untuk periode masa depan
    
    Args:
        model: Model Prophet yang sudah dilatih
        periods: Jumlah hari ke depan untuk diprediksi
    
    Returns:
        future_forecast: DataFrame dengan prediksi
    """
    if model is None:
        return None
    
    try:
        # Buat future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Buat prediksi
        forecast = model.predict(future)
        
        # Ambil hanya prediksi masa depan
        future_forecast = forecast.tail(periods).copy()
        
        # Tambahkan informasi hari
        future_forecast['day_name'] = future_forecast['ds'].dt.strftime('%A')
        future_forecast['date_str'] = future_forecast['ds'].dt.strftime('%Y-%m-%d')
        
        return forecast, future_forecast
        
    except Exception as e:
        st.error(f"Error making predictions: {e}")
        return None, None

# Fungsi untuk evaluasi model Prophet
def evaluate_prophet_model(model, prophet_data):
    """
    Evaluasi performa model Prophet menggunakan cross-validation
    """
    if model is None or prophet_data is None:
        return None
    
    try:
        # Hanya lakukan cross-validation jika data cukup banyak
        if len(prophet_data) < 30:
            return None
        
        # Cross-validation
        df_cv = cross_validation(
            model, 
            initial='15 days',    # Training period minimal
            period='3 days',      # Jarak antar fold
            horizon='7 days',     # Periode prediksi
            parallel="processes"
        )
        
        # Hitung metrics
        df_performance = performance_metrics(df_cv)
        
        return df_performance
        
    except Exception as e:
        st.warning(f"Could not perform cross-validation: {e}")
        return None

# Fungsi untuk membuat chart prediksi Prophet
def create_prophet_chart(model, forecast, future_forecast):
    """
    Membuat chart prediksi Prophet yang interaktif
    """
    if model is None or forecast is None:
        return None
    
    try:
        # Buat plot menggunakan Plotly
        fig = plot_plotly(model, forecast)
        
        # Customize plot
        fig.update_layout(
            title="Coffee Sales Prediction with Facebook Prophet",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            height=600,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Update trace names
        for trace in fig.data:
            if trace.name == 'Actual':
                trace.name = 'Historical Data'
            elif trace.name == 'Forecast':
                trace.name = 'Prediction'
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating Prophet chart: {e}")
        return None

# Fungsi untuk membuat chart komponen Prophet
def create_prophet_components_chart(model, forecast):
    """
    Membuat chart komponen Prophet (trend, seasonality, dll)
    """
    if model is None or forecast is None:
        return None
    
    try:
        fig = plot_components_plotly(model, forecast)
        fig.update_layout(height=800)
        return fig
    except Exception as e:
        st.error(f"Error creating components chart: {e}")
        return None

# Fungsi utama untuk menampilkan dashboard prediksi
def display_prediction_dashboard():
    """
    Fungsi utama untuk menampilkan dashboard prediksi dengan Facebook Prophet
    """
    
    # Load CSS
    load_prediction_css()
    
    # Header
    st.markdown("""
    <div class="prediction-header">
        <h1>🔮 Coffee Sales Prediction</h1>
        <p>Powered by Facebook Prophet - Advanced Time Series Forecasting</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Informasi tentang Facebook Prophet
    st.markdown("""
    <div class="prophet-info">
        <h3>📚 Tentang Facebook Prophet</h3>
        <p><strong>Facebook Prophet</strong> adalah library forecasting yang dikembangkan oleh Facebook untuk prediksi time series. 
        Prophet sangat cocok untuk data bisnis dengan karakteristik:</p>
        <ul>
            <li><strong>Trend</strong>: Pola pertumbuhan atau penurunan jangka panjang</li>
            <li><strong>Seasonality</strong>: Pola berulang (harian, mingguan, tahunan)</li>
            <li><strong>Holiday Effects</strong>: Pengaruh hari libur atau event khusus</li>
            <li><strong>Uncertainty</strong>: Memberikan confidence interval untuk prediksi</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner('Memuat data untuk prediksi...'):
        df = fetch_prediction_data()
    
    if df is None:
        st.error("❌ Tidak dapat memuat data dari database.")
        st.info("💡 Pastikan database sudah terisi dengan data melalui halaman ETL")
        return
    
    if df.empty:
        st.warning("⚠️ Tidak ada data untuk prediksi.")
        return
    
    # Prepare Prophet data
    with st.spinner('Mempersiapkan data untuk Facebook Prophet...'):
        prophet_data, daily_data = prepare_prophet_data(df)
    
    if prophet_data is None:
        st.error("❌ Tidak dapat mempersiapkan data untuk prediksi.")
        st.info("💡 Data mungkin tidak cukup atau format tidak sesuai")
        return
    
    # Tampilkan informasi data
    st.markdown("## 📊 Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Days", len(prophet_data))
    
    with col2:
        st.metric("Date Range", f"{prophet_data['ds'].min().strftime('%Y-%m-%d')} to {prophet_data['ds'].max().strftime('%Y-%m-%d')}")
    
    with col3:
        st.metric("Avg Daily Revenue", f"${prophet_data['y'].mean():,.0f}")
    
    with col4:
        st.metric("Total Revenue", f"${prophet_data['y'].sum():,.0f}")
    
    # Model configuration
    st.markdown("## ⚙️ Model Configuration")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        seasonality_mode = st.selectbox(
            "Seasonality Mode",
            options=['additive', 'multiplicative'],
            index=0,
            help="Additive: seasonality konstan, Multiplicative: seasonality proporsional dengan trend"
        )
        
        prediction_days = st.selectbox(
            "Periode Prediksi",
            options=[3, 7, 14, 30, 60],
            index=1,
            help="Jumlah hari ke depan untuk diprediksi"
        )
    
    with col2:
        st.markdown("### Model Parameters:")
        st.write("- **Growth**: Linear trend")
        st.write("- **Yearly Seasonality**: Enabled")
        st.write("- **Weekly Seasonality**: Enabled")
        st.write("- **Confidence Interval**: 80%")
        st.write("- **Custom Weekend Pattern**: Added")
    
    # Train model
    if st.button("🚀 Train Model & Generate Predictions", type="primary", use_container_width=True):
        
        # Train Prophet model
        with st.spinner('Melatih Facebook Prophet model...'):
            model, historical_forecast = train_prophet_model(prophet_data, seasonality_mode)
        
        if model is None:
            st.error("❌ Gagal melatih model Prophet.")
            return
        
        st.success("✅ Model berhasil dilatih!")
        
        # Make future predictions
        with st.spinner('Membuat prediksi masa depan...'):
            full_forecast, future_forecast = make_prophet_predictions(model, prediction_days)
        
        if full_forecast is None:
            st.error("❌ Gagal membuat prediksi.")
            return
        
        # Display predictions summary
        st.markdown("## 📈 Hasil Prediksi")
        
        # Summary metrics
        total_predicted = future_forecast['yhat'].sum()
        avg_daily = total_predicted / len(future_forecast)
        min_pred = future_forecast['yhat'].min()
        max_pred = future_forecast['yhat'].max()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Total Prediksi</div>
                <div style="font-size: 1.8rem; font-weight: bold;">${total_predicted:,.0f}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">{prediction_days} hari</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Rata-rata Harian</div>
                <div style="font-size: 1.8rem; font-weight: bold;">${avg_daily:,.0f}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">per hari</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Minimum</div>
                <div style="font-size: 1.8rem; font-weight: bold;">${min_pred:,.0f}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">terendah</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="prediction-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">Maximum</div>
                <div style="font-size: 1.8rem; font-weight: bold;">${max_pred:,.0f}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">tertinggi</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Main prediction chart
        st.markdown("### 📊 Visualisasi Prediksi")
        prophet_chart = create_prophet_chart(model, full_forecast, future_forecast)
        if prophet_chart:
            st.plotly_chart(prophet_chart, use_container_width=True)
        
        # Components chart
        st.markdown("### 📈 Analisis Komponen")
        st.info("Chart di bawah menunjukkan dekomposisi prediksi menjadi trend, seasonality, dan komponen lainnya")
        
        components_chart = create_prophet_components_chart(model, full_forecast)
        if components_chart:
            st.plotly_chart(components_chart, use_container_width=True)
        
        # Detailed predictions table
        st.markdown("### 📋 Detail Prediksi Harian")
        
        # Format table data
        table_data = future_forecast[['date_str', 'day_name', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        table_data['yhat'] = table_data['yhat'].round(0).astype(int)
        table_data['yhat_lower'] = table_data['yhat_lower'].round(0).astype(int)
        table_data['yhat_upper'] = table_data['yhat_upper'].round(0).astype(int)
        
        st.dataframe(
            table_data,
            use_container_width=True,
            column_config={
                'date_str': 'Tanggal',
                'day_name': 'Hari',
                'yhat': st.column_config.NumberColumn('Prediksi ($)', format='$%d'),
                'yhat_lower': st.column_config.NumberColumn('Lower Bound ($)', format='$%d'),
                'yhat_upper': st.column_config.NumberColumn('Upper Bound ($)', format='$%d')
            }
        )
        
        # Model evaluation
        st.markdown("## 🔍 Model Evaluation")
        
        with st.spinner('Melakukan evaluasi model...'):
            performance = evaluate_prophet_model(model, prophet_data)
        
        if performance is not None:
            st.markdown("### Cross-Validation Results")
            st.dataframe(performance)
            
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                mae = performance['mae'].mean()
                st.markdown(f"""
                <div class="model-performance">
                    <h4>MAE</h4>
                    <h3>${mae:,.0f}</h3>
                    <small>Mean Absolute Error</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                mape = performance['mape'].mean()
                st.markdown(f"""
                <div class="model-performance">
                    <h4>MAPE</h4>
                    <h3>{mape:.2%}</h3>
                    <small>Mean Absolute Percentage Error</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                coverage = performance['coverage'].mean()
                st.markdown(f"""
                <div class="model-performance">
                    <h4>Coverage</h4>
                    <h3>{coverage:.2%}</h3>
                    <small>Prediction Interval Coverage</small>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.info("Cross-validation tidak dapat dilakukan karena data terbatas. Minimal 30 hari data diperlukan.")
        
        # Business insights
        st.markdown("## 💡 Business Insights")
        
        # Find best and worst days
        best_day_idx = future_forecast['yhat'].idxmax()
        worst_day_idx = future_forecast['yhat'].idxmin()
        
        best_day = future_forecast.loc[best_day_idx]
        worst_day = future_forecast.loc[worst_day_idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="prediction-insight">
                <h4>📈 Hari Terbaik</h4>
                <p><strong>{best_day['day_name']}, {best_day['date_str']}</strong></p>
                <p>Prediksi Revenue: <strong>${best_day['yhat']:,.0f}</strong></p>
                <p>Range: ${best_day['yhat_lower']:,.0f} - ${best_day['yhat_upper']:,.0f}</p>
                <p><em>Pertimbangkan untuk menambah stok dan staff</em></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="warning-card">
                <h4>📉 Hari Terendah</h4>
                <p><strong>{worst_day['day_name']}, {worst_day['date_str']}</strong></p>
                <p>Prediksi Revenue: <strong>${worst_day['yhat']:,.0f}</strong></p>
                <p>Range: ${worst_day['yhat_lower']:,.0f} - ${worst_day['yhat_upper']:,.0f}</p>
                <p><em>Hari untuk maintenance atau promosi khusus</em></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Trend analysis
        st.markdown("### 📊 Trend Analysis")
        
        # Calculate trend from forecast
        trend_start = full_forecast['trend'].iloc[0]
        trend_end = full_forecast['trend'].iloc[-1]
        trend_change = ((trend_end - trend_start) / trend_start) * 100
        
        if trend_change > 0:
            trend_status = "NAIK"
            trend_color = "#28a745"
            trend_icon = "📈"
        elif trend_change < 0:
            trend_status = "TURUN"
            trend_color = "#dc3545"
            trend_icon = "📉"
        else:
            trend_status = "STABIL"
            trend_color = "#ffc107"
            trend_icon = "➡️"
        
        st.markdown(f"""
        <div class="prediction-insight">
            <h4>{trend_icon} Trend Jangka Panjang</h4>
            <p>Status: <strong style="color: {trend_color};">{trend_status}</strong></p>
            <p>Perubahan: <strong>{trend_change:+.2f}%</strong></p>
            <p><em>Berdasarkan analisis trend Prophet model</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer dengan informasi
    st.markdown("---")
    st.markdown("### 📘 Cara Kerja Facebook Prophet")
    
    st.markdown("""
    **Facebook Prophet** bekerja dengan mendekomposisi time series menjadi beberapa komponen:
    
    1. **Trend (g(t))**: Pola pertumbuhan jangka panjang
    2. **Seasonality (s(t))**: Pola berulang (mingguan, tahunan)
    3. **Holiday Effects (h(t))**: Pengaruh hari libur
    4. **Error (ε(t))**: Noise atau variasi acak
    
    **Formula**: y(t) = g(t) + s(t) + h(t) + ε(t)
    
    **Keunggulan Prophet**:
    - Menangani missing data dengan baik
    - Otomatis mendeteksi changepoints
    - Robust terhadap outliers
    - Memberikan uncertainty intervals
    - Mudah untuk interpretasi
    """)
    
    if 'prophet_data' in locals():
        st.info(f"📊 Data Range: {prophet_data['ds'].min().strftime('%Y-%m-%d')} to {prophet_data['ds'].max().strftime('%Y-%m-%d')} | "
                f"🔄 Total Records: {len(prophet_data):,} days | "
                f"🤖 Model: Facebook Prophet")

# Function untuk refresh prediction data
def refresh_prediction_data():
    st.cache_data.clear()
    st.rerun()

if __name__ == "__main__":
    display_prediction_dashboard()