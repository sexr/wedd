# Import modul yang diperlukan dari Bottle dan sqlite3
from bottle import route, run, request, response, static_file, install
import sqlite3
import os
from datetime import datetime
from bottle_cors_plugin import cors_plugin # Import plugin CORS

# --- Konfigurasi Database ---
# Mendapatkan jalur direktori script saat ini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Menentukan jalur database
DATABASE = os.path.join(BASE_DIR, 'comments.db')

# Fungsi untuk terhubung ke database dan membuat tabel jika belum ada
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Mengembalikan baris sebagai objek mirip kamus
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Inisialisasi database saat aplikasi dimulai
init_db()

# --- Konfigurasi CORS (Menggunakan plugin Bottle) ---
# Menginstal plugin CORS ke aplikasi Bottle
# Ini akan menangani preflight (OPTIONS) requests secara otomatis dan menambahkan header CORS
install(cors_plugin(origins=['http://localhost:8080', 'http://0.0.0.0:8080'])) # Izinkan dari localhost dan 0.0.0.0

# --- Rute API ---

# Rute untuk melayani file statis (gambar, video, musik, dll.)
@route('/<filepath:path>')
def serve_static(filepath):
    # Pastikan file statis dilayani dari direktori yang sama dengan script
    # dan juga sub-direktori seperti 'images', 'vid', 'music'
    if os.path.exists(os.path.join(BASE_DIR, filepath)):
        return static_file(filepath, root=BASE_DIR)
    # Jika file tidak ditemukan langsung, coba cari di sub-direktori umum
    elif os.path.exists(os.path.join(BASE_DIR, 'images', filepath)):
        return static_file(filepath, root=os.path.join(BASE_DIR, 'images'))
    elif os.path.exists(os.path.join(BASE_DIR, 'vid', filepath)):
        return static_file(filepath, root=os.path.join(BASE_DIR, 'vid'))
    elif os.path.exists(os.path.join(BASE_DIR, 'music', filepath)):
        return static_file(filepath, root=os.path.join(BASE_DIR, 'music'))
    # Jika tidak ada jalur yang cocok, layani index.html sebagai fallback
    return static_file('index.html', root=BASE_DIR)


# Rute untuk menyajikan halaman utama (index.html)
@route('/')
def index():
    return static_file('index.html', root=BASE_DIR)

# Rute untuk mengirimkan komentar baru
@route('/submit_comment', method='POST')
def submit_comment():
    response.content_type = 'application/json'
    try:
        data = request.json
        name = data.get('name')
        message = data.get('message')

        if not name or not message:
            return {'status': 'error', 'message': 'Nama dan pesan tidak boleh kosong.'}

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (name, message) VALUES (?, ?)", (name, message))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Komentar berhasil ditambahkan.'}
    except Exception as e:
        print(f"Error submitting comment: {e}")
        return {'status': 'error', 'message': 'Terjadi kesalahan internal server.'}

# Rute untuk mendapatkan semua komentar dan jumlah kehadiran
@route('/get_comments', method='GET')
def get_comments():
    response.content_type = 'application/json'
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ambil semua komentar, urutkan berdasarkan waktu terbaru
        comments = cursor.execute("SELECT name, message, timestamp FROM comments ORDER BY timestamp DESC").fetchall()
        
        # Hitung jumlah kehadiran (jumlah komentar unik)
        # Atau jika "jumlah kehadiran" berarti total komentar, gunakan COUNT(*)
        count_cursor = conn.cursor()
        total_comments = count_cursor.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        
        conn.close()

        comments_list = []
        for comment in comments:
            comments_list.append({
                'name': comment['name'],
                'message': comment['message'],
                'timestamp': comment['timestamp'] # Bisa diformat lebih lanjut jika perlu
            })
        
        return {'comments': comments_list, 'count': total_comments}
    except Exception as e:
        print(f"Error getting comments: {e}")
        return {'comments': [], 'count': 0, 'message': 'Gagal memuat komentar.'}

# --- Jalankan Aplikasi ---
# Host '0.0.0.0' agar dapat diakses dari jaringan lokal
# Port 8080 adalah port default yang sering digunakan. PASTIKAN PORT INI SAMA DENGAN DI index.html
run(host='0.0.0.0', port=8080, debug=True, reloader=True)
