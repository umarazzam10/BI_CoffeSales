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
    page = st.sidebar.radio("Pilih Halaman", ["Home", "ETL", "Dashboard"])

    if page == "Home":
        st.title("🏠 Selamat datang di Sistem ETL dan Dashboard")
        st.markdown("""
        ### Sistem Business Intelligence Coffee Shop
        
        **Fitur yang tersedia:**
        - **ETL**: Upload dan proses data CSV ke database
        - **Dashboard**: Visualisasi analytics dan KPI real-time
        
        Silakan pilih halaman di sidebar untuk melanjutkan.
        """)
        
        # Quick stats di home
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📊 Real-time Analytics")
        with col2:
            st.info("🔄 Automated ETL")
        with col3:
            st.info("📈 Business Intelligence")
    
    elif page == "ETL":
        # Memanggil fungsi ETL
        import etl
        etl.display_etl()

    elif page == "Dashboard":
        # Memanggil fungsi Dashboard
        import dashboard
        dashboard.display_dashboard()

if __name__ == "__main__":
    main()