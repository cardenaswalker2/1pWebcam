import os
import zipfile
import random
import shutil

DATA_ROOT = os.path.abspath("data/dataset_yolo")
os.makedirs(os.path.join(DATA_ROOT, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(DATA_ROOT, "images", "val"), exist_ok=True)
os.makedirs(os.path.join(DATA_ROOT, "labels", "train"), exist_ok=True)
os.makedirs(os.path.join(DATA_ROOT, "labels", "val"), exist_ok=True)

zip_path = "dataset.zip"
print("Extrayendo y preparando dataset para YOLO...")

with zipfile.ZipFile(zip_path, 'r') as z:
    all_names = z.namelist()
    
    # Extraer también carpetas útiles para pruebas directas en la app
    for item in all_names:
        if item.startswith("dataset/videos/") and not item.endswith("/"):
            target_path = os.path.join("data", item)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(z.read(item))
        if item.startswith("dataset/test_external/") and not item.endswith("/"):
            target_path = os.path.join("data", item)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(z.read(item))
                
    # Obtener pares de imagen y etiqueta en synthetic
    syn_images = [n for n in all_names if n.startswith("dataset/synthetic/images/") and n.endswith((".png", ".jpg", ".jpeg"))]
    print(f"Total imágenes sintéticas encontradas: {len(syn_images)}")
    
    random.seed(42)
    random.shuffle(syn_images)
    
    val_split = int(len(syn_images) * 0.2)
    val_imgs = set(syn_images[:val_split])
    train_imgs = set(syn_images[val_split:])
    
    for img_path in syn_images:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        ext = os.path.splitext(img_path)[1]
        lbl_path = f"dataset/synthetic/labels/{base_name}.txt"
        
        split = "val" if img_path in val_imgs else "train"
        
        # Guardar imagen
        dst_img = os.path.join(DATA_ROOT, "images", split, f"{base_name}{ext}")
        with open(dst_img, "wb") as f:
            f.write(z.read(img_path))
            
        # Guardar label si existe
        dst_lbl = os.path.join(DATA_ROOT, "labels", split, f"{base_name}.txt")
        if lbl_path in all_names:
            with open(dst_lbl, "wb") as f:
                f.write(z.read(lbl_path))
        else:
            # Archivo vacío para imagen negativa
            open(dst_lbl, "w").close()

# Crear data.yaml
yaml_content = f"""path: {DATA_ROOT.replace('\\', '/')}
train: images/train
val: images/val

names:
  0: defecto_teja
"""

yaml_path = os.path.join(DATA_ROOT, "data.yaml")
with open(yaml_path, "w", encoding="utf-8") as f:
    f.write(yaml_content)

print(f"Dataset estructurado con éxito en: {DATA_ROOT}")
print(f"Archivo data.yaml generado en: {yaml_path}")
