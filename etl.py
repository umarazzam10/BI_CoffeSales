import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import uuid

# Fungsi untuk membuat koneksi ke database MySQL menggunakan SQLAlchemy
def create_connection():
    try:
        # Format: mysql+pymysql://username:password@host:port/database
        DATABASE_URL = "mysql+pymysql://root:@localhost:3306/coffeedw"
        engine = create_engine(DATABASE_URL, echo=False)
        return engine
    except Exception as e:
        st.error(f"Error while connecting to MySQL: {e}")
        return None

# Fungsi untuk mengupload file CSV
def upload_file():
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep=';')
        st.write("Data yang diupload:", df.head())
        return df
    return None

# Fungsi untuk membersihkan dan mentransformasi data (Preprocessing)
def preprocess_data(df):
    st.write("Nama kolom yang ada dalam DataFrame sebelum preprocessing:", df.columns)
    df = df.dropna()
    
    # Mengubah tipe data kolom yang diperlukan
    if 'transaction_date' in df.columns:
        try:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce', dayfirst=True)
            # Cek apakah ada NaT setelah parsing
            if df['transaction_date'].isnull().sum() > 0:
                st.warning("Beberapa tanggal tidak valid dan diubah menjadi NaT.")
        except Exception as e:
            st.error(f"Error parsing 'transaction_date': {e}")
    
    if 'transaction_qty' in df.columns:
        df['transaction_qty'] = df['transaction_qty'].astype(int)
    
    if 'unit_price' in df.columns:
        df['unit_price'] = df['unit_price'].astype(float)
    
    if 'Total_Bill' in df.columns:
        df['Total_Bill'] = df['Total_Bill'].astype(float)
    
    # Membuat kolom time_id sebagai UUID
    df['time_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    
    # Ubah format 'transaction_date'
    df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.write("Nama kolom yang ada dalam DataFrame setelah preprocessing:", df.columns)
    st.write("Data setelah preprocessing:", df.head())
    
    return df

# Fungsi untuk memasukkan data ke dalam MySQL menggunakan SQLAlchemy
def load_to_mysql(df):
    engine = create_connection()
    if engine is not None:
        try:
            with engine.begin() as conn:  # Menggunakan transaction
                
                # Insert data ke dim_time
                dim_time_data = []
                for index, row in df.iterrows():
                    time_id = row.get('time_id', None)
                    if time_id is None:
                        st.warning(f"Warning: time_id tidak ditemukan untuk baris {index}")
                        continue
                    
                    transaction_date = row.get('transaction_date', None)
                    if transaction_date is None:
                        st.warning(f"Warning: transaction_date tidak ditemukan untuk baris {index}")
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
                
                st.success("Data berhasil dimuat ke dalam MySQL")
                
        except Exception as e:
            st.error(f"Error loading data to MySQL: {e}")
    else:
        st.error("Tidak dapat terhubung ke database MySQL")

def display_etl():
    st.title("Sistem ETL BI dengan Preprocessing")
    
    # Upload file CSV
    df = upload_file()
    if df is not None:
        # Preprocessing data
        df_processed = preprocess_data(df)
        
        # Tombol untuk memuat data ke MySQL
        if st.button("Load Data ke MySQL"):
            load_to_mysql(df_processed)

if __name__ == "__main__":
    display_etl()