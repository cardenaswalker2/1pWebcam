import os
import shutil
from ultralytics import YOLO

def train():
    print("Iniciando entrenamiento ultraligero de YOLOv8n para detección de defectos en tejas...")
    model = YOLO("yolov8n.pt")  # Descarga pesos base oficiales si no están
    
    data_yaml = os.path.abspath("data/dataset_yolo/data.yaml")
    
    # Entrenar por 15 épocas (rápido en CPU pero con suficiente convergencia para detectar las fallas)
    results = model.train(
        data=data_yaml,
        epochs=15,
        imgsz=640,
        batch=8,
        workers=2,
        device="cpu",
        project="runs_train",
        name="tejas_defectos",
        exist_ok=True
    )
    
    best_weights = os.path.join("runs_train", "tejas_defectos", "weights", "best.pt")
    target_weights = os.path.join("models", "yolov8_custom.pt")
    
    if os.path.exists(best_weights):
        shutil.copy(best_weights, target_weights)
        print(f"✅ ¡Modelo entrenado exitosamente! Pesos guardados en: {target_weights}")
    else:
        last_weights = os.path.join("runs_train", "tejas_defectos", "weights", "last.pt")
        if os.path.exists(last_weights):
            shutil.copy(last_weights, target_weights)
            print(f"✅ Pesos guardados en: {target_weights}")

if __name__ == "__main__":
    train()
