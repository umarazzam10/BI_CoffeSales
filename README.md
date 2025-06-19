# ☕ Coffee Analytics System

Sistem Business Intelligence yang dirancang khusus untuk coffee shop modern dengan fitur ETL (Extract, Transform, Load), Analytics Dashboard, dan Predictive Analytics.

## 🚀 Fitur Utama:

1. Home
2. 🔄 ETL Process

- **Extract**: Upload data CSV terkait transaksi penjualan coffeeshop
- **Transform**: Pembersihan dan transformasi data otomatis
- **Load**: Muat data ke database MySQL dengan struktur data warehouse

3. 📊 Analytics Dashboard
4. 🔮 Predictive Analytics

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Database**: MySQL 8.0+
- **Visualization**: Plotly
- **Data Processing**: Pandas, NumPy
- **Model untuk prediksi**: FB Prophet
- **Database Connector**: SQLAlchemy, PyMySQL

## 🏗️ Arsitektur Sistem

```
📁 Data Sources (CSV)
        ↓
🔄 ETL Process
        ↓
🗄️ MySQL Data Warehouse
        ↓
📊 Analytics Dashboard
        ↓
📈 Prediction
       ↓
📈 Business Insights
```

## 📋 Prasyarat

Pastikan sistem Anda memiliki:

- **Python 3.8 atau lebih tinggi**
- **MySQL Server 8.0 atau lebih tinggi**
- **Minimal 4GB RAM** (untuk processing data besar)

## 🔧 Instalasi

### 1. Simpan folder project BI_CoffeSales

## 📝 File Struktur Project

CoffeSales_Project_BI/
│
├── main.py # File utama aplikasi
├── etl_script.py # Module ETL process
├── dashboard.py # Module dashboard analytics
├── prediction.py # Module predictive analytics
├── requirements.txt # Dependencies Python
├── README.md # Dokumentasi ini
│
├── dataset.csv

### 2. Buat Virtual Environment (Opsional namun direkomendasikan)

python -m venv venv
lalu Aktifkan Virtual Environment dengan kode :

# Windows

venv\Scripts\activate

# macOS/Linux

source venv/bin/activate

### 3. Install Dependencies

install sekaligus dengan :
pip install -r requirements.txt

ataupun install manual satu per satu:
pip install streamlit pandas numpy plotly sqlalchemy pymysql prophet

### 4. Import Database

-buat database MySQL dengan nama coffeedw
-import file SQL coffeedw pada mysql

## 🚀 Menjalankan Aplikasi

### 1. Aktivasi Virtual Environment

Jika menggunakan venv, maka aktivasi dulu. Jika tidak, maka langsung lanjut ke step 2

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Jalankan Aplikasi

```bash
streamlit run main.py
```

### 3. Akses Aplikasi

Buka browser dan akses: `http://localhost:8501`
