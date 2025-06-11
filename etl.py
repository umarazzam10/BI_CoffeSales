import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import uuid



# Custom CSS untuk styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
        
    

    
    .step-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #8B4513;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .step-number {
        background: #8B4513;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
    }
    
    .step-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #8B4513;
        margin-bottom: 0.5rem;
    }
    
    .step-description {
        color: #666;
        line-height: 1.6;
    }
    
    /* File uploader styling */
    .stFileUploader > div > div > div {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px dashed #8B4513;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 69, 19, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 69, 19, 0.4);
    }
    
    /* Progress indicators */
    .progress-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Data preview styling */
    .dataframe-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>☕ Coffee Analytics ETL System </h1>
        <p>Extract, Transform & Load untuk Coffee Shop Business Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

# Fungsi untuk membuat koneksi ke database MySQL menggunakan SQLAlchemy
def create_connection():
    try:
        # Format: mysql+pymysql://username:password@host:port/database
        DATABASE_URL = "mysql+pymysql://root:@localhost:3306/coffeedw"
        engine = create_engine(DATABASE_URL, echo=False)
        return engine
    except Exception as e:
        st.error(f"❌ Error while connecting to MySQL: {e}")
        return None

# Fungsi untuk mengupload file CSV
def upload_file():
    st.markdown("""
    <div class="step-card">
        <div style="display: flex; align-items: center;">
            <span class="step-number">1</span>
            <div>
                <div class="step-title">📁 Extract (Upload Data CSV)</div>
                <div class="step-description">Pilih file CSV yang berisi data transaksi coffee shop untuk diproses</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Pilih file CSV", 
        type=["csv"],
        help="Upload file CSV yang berisi data transaksi coffee shop"
    )
    
    if uploaded_file is not None:
        with st.spinner('🔍 Menganalisis format file...'):
            # Coba deteksi separator otomatis
            sample = uploaded_file.read(1024).decode('utf-8')
            uploaded_file.seek(0)  # Reset file pointer
            
            # Hitung frekuensi separator yang mungkin
            comma_count = sample.count(',')
            semicolon_count = sample.count(';')
            tab_count = sample.count('\t')
            
            # Tentukan separator berdasarkan frekuensi tertinggi
            if comma_count > semicolon_count and comma_count > tab_count:
                separator = ','
            elif semicolon_count > comma_count and semicolon_count > tab_count:
                separator = ';'
            elif tab_count > 0:
                separator = '\t'
            else:
                separator = ','  # default
            
            st.info(f"🔧 Separator yang dideteksi: **'{separator}'**")
            
            try:
                df = pd.read_csv(uploaded_file, sep=separator)
                
                # Display file info in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Jumlah Baris", f"{len(df):,}")
                with col2:
                    st.metric("📋 Jumlah Kolom", len(df.columns))
                with col3:
                    st.metric("💾 Ukuran Data", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                
                # Show column names
                st.markdown("**📝 Kolom yang ditemukan:**")
                cols_display = " • ".join(df.columns.tolist())
                st.markdown(f"<div style='background:#f8f9fa; padding:1rem; border-radius:8px; margin:1rem 0;'>{cols_display}</div>", unsafe_allow_html=True)
                
                # Data preview
                st.markdown("**👀 Preview Data:**")
                st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                st.dataframe(df.head(), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                return df
                
            except Exception as e:
                st.error(f"❌ Error membaca CSV dengan separator '{separator}': {e}")
                # Coba dengan separator lain secara berurutan
                separators_to_try = [',', ';', '\t', '|']
                uploaded_file.seek(0)
                
                for sep in separators_to_try:
                    try:
                        df = pd.read_csv(uploaded_file, sep=sep)
                        if len(df.columns) > 1:  # Pastikan kolom terparsing dengan benar
                            st.success(f"✅ Berhasil dengan separator '{sep}'")
                            st.write(f"📊 Jumlah kolom: {len(df.columns)}")
                            st.write("📝 Nama kolom:", df.columns.tolist())
                            st.dataframe(df.head())
                            return df
                        uploaded_file.seek(0)
                    except:
                        uploaded_file.seek(0)
                        continue
                
                st.error("❌ Gagal membaca file CSV dengan berbagai separator")
                return None
    return None

# Fungsi untuk membersihkan dan mentransformasi data (Preprocessing)
def preprocess_data(df):
    st.markdown("""
    <div class="step-card">
        <div style="display: flex; align-items: center;">
            <span class="step-number">2</span>
            <div>
                <div class="step-title">🔄 Transform</div>
                <div class="step-description">Membersihkan dan mentransformasi data sebelum dimuat ke database</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner('⚙️ Memproses data...'):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text('🧹 Membersihkan data kosong...')
        progress_bar.progress(20)
        
        initial_rows = len(df)
        df = df.dropna()
        cleaned_rows = len(df)
        
        if initial_rows > cleaned_rows:
            st.warning(f"⚠️ Dihapus {initial_rows - cleaned_rows} baris yang mengandung data kosong")
        
        status_text.text('📅 Memproses kolom tanggal...')
        progress_bar.progress(40)
        
        # Mengubah tipe data kolom yang diperlukan
        if 'transaction_date' in df.columns:
            try:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce', dayfirst=True)
                # Cek apakah ada NaT setelah parsing
                if df['transaction_date'].isnull().sum() > 0:
                    st.warning("⚠️ Beberapa tanggal tidak valid dan diubah menjadi NaT.")
            except Exception as e:
                st.error(f"❌ Error parsing 'transaction_date': {e}")
        
        status_text.text('🔢 Mengkonversi tipe data numerik...')
        progress_bar.progress(60)
        
        if 'transaction_qty' in df.columns:
            df['transaction_qty'] = df['transaction_qty'].astype(int)
        
        if 'unit_price' in df.columns:
            df['unit_price'] = df['unit_price'].astype(float)
        
        if 'Total_Bill' in df.columns:
            df['Total_Bill'] = df['Total_Bill'].astype(float)
        
        status_text.text('🆔 Membuat ID unik untuk waktu...')
        progress_bar.progress(80)
        
        # Membuat kolom time_id sebagai UUID
        df['time_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        # Ubah format 'transaction_date'
        df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        status_text.text('✅ Preprocessing selesai!')
        progress_bar.progress(100)
        
        # Show preprocessing results
        st.success("🎉 Data berhasil diproses!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 Kolom Sebelum Preprocessing:**")
            st.code('\n'.join([f"• {col}" for col in df.columns if col != 'time_id']))
        
        with col2:
            st.markdown("**📋 Kolom Setelah Preprocessing:**")
            st.code('\n'.join([f"• {col}" for col in df.columns]))
        
        st.markdown("**👀 Data Setelah Preprocessing:**")
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(df.head(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
    
    return df

# Fungsi untuk memasukkan data ke dalam MySQL menggunakan SQLAlchemy
def load_to_mysql(df):
    st.markdown("""
    <div class="step-card">
        <div style="display: flex; align-items: center;">
            <span class="step-number">3</span>
            <div>
                <div class="step-title">💾 Load to Database</div>
                <div class="step-description">Memuat data ke dalam database MySQL dengan struktur data warehouse</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    engine = create_connection()
    if engine is not None:
        try:
            with st.spinner('🔄 Memuat data ke database...'):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with engine.begin() as conn:  # Menggunakan transaction
                    
                    status_text.text('📅 Memuat data dimensi waktu...')
                    progress_bar.progress(25)
                    
                    # Insert data ke dim_time
                    dim_time_data = []
                    for index, row in df.iterrows():
                        time_id = row.get('time_id', None)
                        if time_id is None:
                            st.warning(f"⚠️ Warning: time_id tidak ditemukan untuk baris {index}")
                            continue
                        
                        transaction_date = row.get('transaction_date', None)
                        if transaction_date is None:
                            st.warning(f"⚠️ Warning: transaction_date tidak ditemukan untuk baris {index}")
                            continue
                        
                        transaction_time = row.get('transaction_time', None)
                        month_name = row.get('Month Name', None)
                        day_name = row.get('Day Name', None)
                        day_of_week = row.get('Day of Week', None)
                        hour = row.get('Hour', None)
                        
                        year = transaction_date[:4]
                        month = transaction_date[5:7]
                        day = transaction_date[8:10]
                        
                        dim_time_data.append({
                            'time_id': time_id,
                            'transaction_date': transaction_date,
                            'transaction_time': transaction_time,
                            'year': year,
                            'month': month,
                            'month_name': month_name,
                            'day': day,
                            'day_name': day_name,
                            'day_of_week': day_of_week,
                            'hour': hour
                        })
                    
                    # Convert to DataFrame dan insert ke dim_time
                    if dim_time_data:
                        df_dim_time = pd.DataFrame(dim_time_data)
                        df_dim_time.to_sql('dim_time', conn, if_exists='append', index=False, method='multi')
                    
                    status_text.text('🛍️ Memuat data dimensi produk...')
                    progress_bar.progress(50)
                    
                    # Insert data ke dim_product
                    dim_product_data = []
                    for index, row in df.iterrows():
                        dim_product_data.append({
                            'product_id': row['product_id'],
                            'product_category': row['product_category'],
                            'product_type': row['product_type'],
                            'product_detail': row['product_detail'],
                            'size': row['Size']
                        })
                    
                    if dim_product_data:
                        df_dim_product = pd.DataFrame(dim_product_data)
                        df_dim_product.drop_duplicates().to_sql('dim_product', conn, if_exists='append', index=False, method='multi')
                    
                    status_text.text('🏪 Memuat data dimensi toko...')
                    progress_bar.progress(75)
                    
                    # Insert data ke dim_store
                    dim_store_data = []
                    for index, row in df.iterrows():
                        dim_store_data.append({
                            'store_id': row['store_id'],
                            'store_location': row['store_location']
                        })
                    
                    if dim_store_data:
                        df_dim_store = pd.DataFrame(dim_store_data)
                        df_dim_store.drop_duplicates().to_sql('dim_store', conn, if_exists='append', index=False, method='multi')
                    
                    status_text.text('💰 Memuat data fakta penjualan...')
                    progress_bar.progress(90)
                    
                    # Insert data ke fact_sales
                    fact_sales_data = []
                    for index, row in df.iterrows():
                        fact_sales_data.append({
                            'transaction_id': row['transaction_id'],
                            'time_id': row['time_id'],
                            'product_id': row['product_id'],
                            'store_id': row['store_id'],
                            'transaction_qty': row['transaction_qty'],
                            'unit_price': row['unit_price'],
                            'total_bill': row['Total_Bill']
                        })
                    
                    if fact_sales_data:
                        df_fact_sales = pd.DataFrame(fact_sales_data)
                        df_fact_sales.to_sql('fact_sales', conn, if_exists='append', index=False, method='multi')
                    
                    progress_bar.progress(100)
                    status_text.text('✅ Semua data berhasil dimuat!')
                    
                    # Show success metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📅 Dim Time", len(dim_time_data))
                    with col2:
                        st.metric("🛍️ Dim Product", len(set(row['product_id'] for row in dim_product_data)))
                    with col3:
                        st.metric("🏪 Dim Store", len(set(row['store_id'] for row in dim_store_data)))
                    with col4:
                        st.metric("💰 Fact Sales", len(fact_sales_data))
                    
                    st.success("🎉 Data berhasil dimuat ke dalam MySQL database!")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
        except Exception as e:
            st.error(f"❌ Error loading data to MySQL: {e}")
    else:
        st.error("❌ Tidak dapat terhubung ke database MySQL")

def display_etl():
    # Main content area
    st.markdown('<div class="etl-card">', unsafe_allow_html=True)
    
    # Upload file CSV
    df = upload_file()
    
    if df is not None:
        # Preprocessing data
        df_processed = preprocess_data(df)
        
        # Load to MySQL section
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Load Data ke MySQL", use_container_width=True):
                load_to_mysql(df_processed)
    
    else:
        # Show instructions when no file is uploaded
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-radius: 15px; margin: 2rem 0;">
            <h3 style="color: #8B4513; margin-bottom: 1rem;">🚀 Mulai Proses ETL</h3>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
                Upload file CSV Anda untuk memulai proses Extract, Transform, dan Load ke database Coffee Analytics
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
                    <div style="font-weight: 600; color: #8B4513;">Extract</div>
                    <div style="color: #666; font-size: 0.9rem;">Upload & Baca CSV</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔄</div>
                    <div style="font-weight: 600; color: #8B4513;">Transform</div>
                    <div style="color: #666; font-size: 0.9rem;">Preprocessing Data</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">💾</div>
                    <div style="font-weight: 600; color: #8B4513;">Load</div>
                    <div style="color: #666; font-size: 0.9rem;">Simpan ke Database</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    display_etl()