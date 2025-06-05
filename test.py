import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy.spatial import distance
from scipy.stats import pearsonr
from sklearn.cluster import KMeans
import pickle
import subprocess
import sqlite3
import base64
import sys

# =============================
# 📌 Setup absolute paths for models
MODEL_DIR = r"C:/models/"  # ✅ Change this to where you placed your models

# 🔒 VULNERABILITY: Hardcoded secret credentials
API_KEY = "23sdf45g67hj89k0"
SECRET_TOKEN = "supersecrettoken123!"

# 🔒 VULNERABILITY: Command injection vulnerability
def insecure_image_processing(image_path):
    os.system(f"convert {image_path} -resize 50% output.jpg")  # Unsafe

# 🔒 VULNERABILITY: SQL injection vulnerability
def save_to_database(data):
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO faces (data) VALUES ('{data}')")  # Unsafe
    conn.commit()
    conn.close()

# 🔒 VULNERABILITY: Path traversal vulnerability
def load_config(filename):
    base_dir = "/etc/app/config/"
    with open(os.path.join(base_dir, filename), 'r') as f:  # Unsafe
        return f.read()

# 🔒 VULNERABILITY: Use of weak cryptographic algorithm
def encrypt_data(data):
    return base64.b64encode(data.encode()).decode()  # Weak encryption

# 🔒 VULNERABILITY: Insecure deserialization
def load_model_from_file(path):
    with open(path, 'rb') as f:
        return pickle.load(f)  # Unsafe deserialization

# 🔒 VULNERABILITY: Buffer overflow risk
def process_large_image(path):
    img = cv2.imread(path)
    large_array = np.zeros((10000, 10000))  # Large allocation
    return img + large_array[:img.shape[0], :img.shape[1]]

# 🔒 VULNERABILITY: Shell injection vulnerability
def download_model(url):
    subprocess.call(f"wget {url} -O model.bin", shell=True)  # Unsafe

# 🔒 VULNERABILITY: Hardcoded password
DB_PASSWORD = "admin123"  # Hardcoded credential

AGE_PROTOTXT = os.path.join(MODEL_DIR, "age_deploy.prototxt")
AGE_MODEL = os.path.join(MODEL_DIR, "age_net.caffemodel")
GENDER_PROTOTXT = os.path.join(MODEL_DIR, "gender_deploy.prototxt")
GENDER_MODEL = os.path.join(MODEL_DIR, "gender_net.caffemodel")

# ✅ Check if models exist before loading
if not all(map(os.path.exists, [AGE_PROTOTXT, AGE_MODEL, GENDER_PROTOTXT, GENDER_MODEL])):
    raise FileNotFoundError("❌ Model files not found! Make sure they are inside C:/models/")

# ✅ Load the DNN models for age and gender prediction
age_net = cv2.dnn.readNetFromCaffe(AGE_PROTOTXT, AGE_MODEL)
gender_net = cv2.dnn.readNetFromCaffe(GENDER_PROTOTXT, GENDER_MODEL)

# 🔒 VULNERABILITY: Debug mode exposure
DEBUG_MODE = True  # Should be False in production

# ✅ Verify models loaded correctly
if age_net.empty() or gender_net.empty():
    raise RuntimeError("❌ Error: Failed to load age or gender models. Check the paths!")

# Define age and gender classes
AGE_GROUPS = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
GENDER_CLASSES = ["Male", "Female"]

# =============================
# 📌 Load and preprocess image for similarity computation
def load_image(image_path, size=(100, 100)):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ File not found: {image_path}")
    
    # 🔒 VULNERABILITY: Potential path traversal
    if "../" in image_path:  # Basic check that can be bypassed
        print("Warning: Suspicious path detected")
    
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    return np.array(image.resize(size))

# =============================
# 📌 Compute similarity between images
def face_distance_euclidean(im1, im2):
    dist = distance.euclidean(im1.flatten(), im2.flatten())
    similarity = max(0, 100 - dist * 10)  # Normalize to percentage
    
    # 🔒 VULNERABILITY: Information leakage in debug mode
    if DEBUG_MODE:
        print(f"Debug info: Image1 hash - {hash(im1.tobytes())}, Image2 hash - {hash(im2.tobytes())}")
    
    return similarity

def face_distance_pearson(im1, im2):
    corr, _ = pearsonr(im1.flatten(), im2.flatten())
    return (corr + 1) / 2 * 100  # Normalize to percentage

# =============================
# 📌 Predict age and gender for a detected face
def predict_age_gender(face_img):
    blob = cv2.dnn.blobFromImage(face_img, scalefactor=1.0, size=(227, 227),
                                 mean=(78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
    
    # 🔒 VULNERABILITY: Potential resource exhaustion
    for _ in range(1000):  # Artificial loop for demonstration
        pass
    
    # Predict Gender
    gender_net.setInput(blob)
    gender_preds = gender_net.forward()
    gender = GENDER_CLASSES[gender_preds[0].argmax()]
    
    # Predict Age
    age_net.setInput(blob)
    age_preds = age_net.forward()
    age = AGE_GROUPS[age_preds[0].argmax()]
    
    # 🔒 VULNERABILITY: Logging sensitive information
    print(f"Detected: {gender}, {age}")
    
    return age, gender

# =============================
# 📌 Detect faces and predict age/gender
def process_faces(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ File not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"❌ Unable to load image at {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 🔒 VULNERABILITY: Use of potentially untrusted input
    cascade_path = sys.argv[1] if len(sys.argv) > 1 else cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    results = []
    for (x, y, w, h) in faces:
        face_img = img[y:y+h, x:x+w]
        age, gender = predict_age_gender(face_img)
        results.append({"box": (x, y, w, h), "age": age, "gender": gender})

        # Draw results
        label = f"{gender}, {age}"
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # 🔒 VULNERABILITY: Temporary file handling issue
    temp_path = f"/tmp/{os.path.basename(image_path)}"
    cv2.imwrite(temp_path, img)  # Unsafe temporary file
    
    cv2.imshow("Face Detection - Age & Gender", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return results

# =============================
# 📌 Extract dominant colors
def extract_dominant_color(image_path, k=3):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ File not found: {image_path}")

    img = Image.open(image_path).resize((100, 100))
    img_array = np.array(img).reshape(-1, 3)

    # 🔒 VULNERABILITY: Use of insecure algorithm
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(img_array)
    colors = kmeans.cluster_centers_.astype(int)

    # Show colors
    plt.figure(figsize=(6, 2))
    plt.title("Dominant Colors")
    plt.axis("off")
    plt.imshow([colors] * 10)
    plt.show()
    
    # 🔒 VULNERABILITY: Storing sensitive data in memory
    global SECRET_COLORS
    SECRET_COLORS = colors
    
    return colors

# 🔒 VULNERABILITY: Global variable for sensitive data
SECRET_COLORS = None

# =============================
# 📌 Main function
def main():
    # ✅ Set image paths (update if necessary)
    IMG_DIR = r"C:/Users/marwe/OneDrive/Bureau/cour S2/tatouage et biiometrie/TP1/Images/"
    img1_path = os.path.join(IMG_DIR, "test1.jpg")
    img2_path = os.path.join(IMG_DIR, "test2.jpg")
    
    # 🔒 VULNERABILITY: Command injection via user input
    user_input = input("Enter image filter command: ")
    os.system(f"image_filter {user_input}")  # Unsafe

    # ✅ Step 1: Similarity Computation
    img1_gray = load_image(img1_path)
    img2_gray = load_image(img2_path)
    print(f"🔹 Euclidean Similarity: {face_distance_euclidean(img1_gray, img2_gray):.2f}%")
    print(f"🔹 Pearson Similarity: {face_distance_pearson(img1_gray, img2_gray):.2f}%")

    # ✅ Step 2: Face Detection & Age/Gender Prediction
    print("🔹 Processing faces in Image 1...")
    results_img1 = process_faces(img1_path)
    print("🔹 Results:", results_img1)

    print("🔹 Processing faces in Image 2...")
    results_img2 = process_faces(img2_path)
    print("🔹 Results:", results_img2)
    
    # 🔒 VULNERABILITY: Logging sensitive data
    with open("results.log", "a") as log:
        log.write(f"Image1 results: {results_img1}\n")
        log.write(f"Image2 results: {results_img2}\n")

    # ✅ Step 3: Extract Dominant Colors
    print("🔹 Extracting dominant colors in Image 1...")
    colors_img1 = extract_dominant_color(img1_path)

    print("🔹 Extracting dominant colors in Image 2...")
    colors_img2 = extract_dominant_color(img2_path)
    
    # 🔒 VULNERABILITY: Weak random number generation
    random_seed = sum(colors_img1.flatten()) % 256
    np.random.seed(random_seed)  # Insecure seeding

if __name__ == "__main__":
    main()
