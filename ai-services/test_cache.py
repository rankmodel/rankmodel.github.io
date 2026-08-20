import time
from context_engine import get_context_db

def run_smoke_test():
    print("Initializing ContextDB...")
    db = get_context_db()
    
    test_path = "context_engine.py"
    
    print("\n--- Testing get_file_context ---")
    start = time.time()
    res1 = db.get_file_context(test_path)
    dur1 = time.time() - start
    print(f"First call took {dur1:.4f} seconds")
    
    start = time.time()
    res2 = db.get_file_context(test_path)
    dur2 = time.time() - start
    print(f"Second call took {dur2:.4f} seconds")
    
    assert res1 == res2, "Results should be identical"
    if dur2 < dur1:
        print("✅ Cache hit successful: second call was faster.")
    else:
        print("⚠️ Second call wasn't strictly faster, but results match.")

if __name__ == '__main__':
    run_smoke_test()
