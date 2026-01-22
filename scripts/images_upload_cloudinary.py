import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY_CLOUDINARY"),
    api_secret=os.getenv("API_SECRET_CLOUDINARY"),
    secure=True
)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
SKIP_UNTIL = "Humour"
RESUME_AFTER = True

def upload_one(path: str, rel_path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    
    public_id = rel_path.replace("\\", "/").rsplit('.', 1)[0]
    
    return cloudinary.uploader.upload(
        path,
        public_id=public_id,
        use_filename=True,
        unique_filename=False,
        overwrite=True
    )["secure_url"]

def upload_all(root="data/dataset"):
    uploaded = []
    skipped = []
    skip_mode = RESUME_AFTER
    folder_found = False
    
    for dirpath, _, filenames in os.walk(root):
        folder_name = os.path.basename(dirpath)
        
        # Проверяем, достигли ли нужной папки
        if skip_mode and folder_name == SKIP_UNTIL:
            folder_found = True
            print(f"⏭️  Пропускаем папку '{SKIP_UNTIL}' и всё до неё...")
            continue
        
        # Если нашли Medical и RESUME_AFTER=True, начинаем загружать после неё
        if folder_found and folder_name != SKIP_UNTIL:
            skip_mode = False
            print(f"▶️  Начинаем загрузку с папки '{folder_name}'...")
        
        if skip_mode:
            continue
        
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                skipped.append(fname)
                continue
            
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            
            try:
                url = upload_one(full, rel_path=rel)
                uploaded.append(url)
                print("✓ Uploaded:", rel)
            except Exception as e:
                print(f"✗ Failed {rel}: {e}")
                skipped.append(rel)
    
    print(f"\n✓ Uploaded: {len(uploaded)}")
    print(f"✗ Skipped: {len(skipped)}")
    if skipped:
        print(f"Skipped files (first 5): {skipped[:5]}")

if __name__ == "__main__":
    upload_all()