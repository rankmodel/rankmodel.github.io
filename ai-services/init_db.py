import sqlite3
import os
import sys

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

def init_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 1. SQLite
    db_path = os.path.join(data_dir, 'memory.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            content TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id TEXT PRIMARY KEY,
            type TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("SQLite memory.db initialized.")
    
    # 2. ChromaDB (Fallback handled)
    vector_dir = os.path.join(data_dir, 'vectors')
    os.makedirs(vector_dir, exist_ok=True)
    
    if CHROMA_AVAILABLE:
        try:
            client = chromadb.PersistentClient(path=vector_dir)
            collection = client.get_or_create_collection(name="embeddings")
            print("ChromaDB initialized at /vectors.")
        except Exception as e:
            print(f"ChromaDB initialization failed: {e}. Falling back to SQLite-only mode.")
    else:
        print("chromadb module not found. Falling back to SQLite-only mode.")
        
    print("DB ready")

if __name__ == '__main__':
    init_db()
