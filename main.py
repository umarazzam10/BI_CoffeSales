import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Coffee Analytics System",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("☕ Coffee Analytics System")
    st.sidebar.markdown("---")
    page = st.sidebar.selectbox(
        "Pilih Halaman",
        ["🏠 Home", "🔄 ETL", "📊 Analytics Dashboard", "🔮 Prediction"]
    )

    if page == "🏠 Home":
        st.title("🏠 Selamat datang di Sistem ETL dan Dashboard")
        st.markdown("""
        ### Sistem Business Intelligence Coffee Shop
        
        **Fitur yang tersedia:**
        - **ETL**: Upload dan proses data CSV ke database
        - **Dashboard**: Visualisasi analytics dan KPI real-time
        """)
        
        # Quick stats di home
        # Hero section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            Sistem Business Intelligence yang dirancang khusus untuk coffee shop modern. 
            Dengan sistem ini, Anda dapat:
            
            ### 🔄 ETL Process
            - **Extract**: Upload data CSV dari sistem POS
            - **Transform**: Pembersihan dan transformasi data otomatis
            - **Load**: Muat data ke database MySQL dengan struktur data warehouse
            
            ### 📊 Analytics Dashboard
            - **Real-time KPI**: Monitor performa bisnis secara real-time
            - **Trend Analysis**: Analisis tren penjualan dan customer behavior
            - **Product Performance**: Pantau produk terlaris dan revenue
            - **Store Comparison**: Bandingkan performa antar cabang
            - **Peak Hours Analysis**: Analisis jam sibuk untuk optimasi staffing
            - **Predictive Analytics**: Prediksi revenue dan demand
            
            ### 🎯 Key Features
            - Dashboard interaktif dengan visualisasi modern
            - Real-time data processing
            - Automated data cleaning dan preprocessing
            - Multi-store analysis
            - Mobile-responsive design
            """)
        
        with col2:
            st.markdown("""
            ### 📋 System Architecture
            
            ```
            📁 Data Sources (CSV)
                    ↓
            🔄 ETL Process
                    ↓
            🗄️ MySQL Data Warehouse
                    ↓
            📊 Analytics Dashboard
                    ↓
            📈 Business Insights
            ```
            
            ### 🛠️ Tech Stack
            - **Frontend**: Streamlit
            - **Backend**: Python
            - **Database**: MySQL
            - **Visualization**: Plotly
            - **Processing**: Pandas
            """)
        
        # Quick stats atau info tambahan
        st.markdown("---")
        st.markdown("### 🚀 Quick Start")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 1️⃣ Upload Data
            Gunakan halaman **ETL Process** untuk upload file CSV dari sistem POS Anda.
            """)
        
        with col2:
            st.markdown("""
            #### 2️⃣ Process Data
            Data akan otomatis dibersihkan dan dimuat ke database.
            """)
        
        with col3:
            st.markdown("""
            #### 3️⃣ View Analytics
            Lihat insights bisnis di halaman **Analytics Dashboard**.
            """)
        
        # Database schema info
        st.markdown("---")
        st.markdown("### 🗄️ Database Schema")
        
        with st.expander("Lihat Database Schema"):
            st.markdown("""
            **Fact Table:**
            - `fact_sales`: Data transaksi utama
            
            **Dimension Tables:**
            - `dim_time`: Dimensi waktu (tanggal, jam, hari, bulan)
            - `dim_product`: Dimensi produk (kategori, tipe, detail)
            - `dim_store`: Dimensi toko (lokasi, cabang)
            
            **Relationships:**
            - Star schema dengan fact_sales sebagai center
            - Foreign keys menghubungkan semua dimension tables
            """)
    
    elif page == "🔄 ETL":
        # Memanggil fungsi ETL
        import etl
        etl.display_etl()

    elif page == "📊 Analytics Dashboard":
        # Memanggil fungsi Dashboard
        import dashboard
        dashboard.display_dashboard()

    elif page == "🔮 Prediction":
        # Memanggil fungsi Prediction
        import prediction
        prediction.display_prediction_dashboard()

if __name__ == "__main__":
    main()