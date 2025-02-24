import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy.spatial import distance
from scipy.stats import pearsonr
from sklearn.cluster import KMeans

# =============================
# 📌 Setup absolute paths for models
MODEL_DIR = r"C:/models/"  # ✅ Change this to where you placed your models

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
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    return np.array(image.resize(size))

# =============================
# 📌 Compute similarity between images
def face_distance_euclidean(im1, im2):
    dist = distance.euclidean(im1.flatten(), im2.flatten())
    similarity = max(0, 100 - dist * 10)  # Normalize to percentage
    return similarity

def face_distance_pearson(im1, im2):
    corr, _ = pearsonr(im1.flatten(), im2.flatten())
    return (corr + 1) / 2 * 100  # Normalize to percentage

# =============================
# 📌 Predict age and gender for a detected face
def predict_age_gender(face_img):
    blob = cv2.dnn.blobFromImage(face_img, scalefactor=1.0, size=(227, 227),
                                 mean=(78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
    # Predict Gender
    gender_net.setInput(blob)
    gender_preds = gender_net.forward()
    gender = GENDER_CLASSES[gender_preds[0].argmax()]
    
    # Predict Age
    age_net.setInput(blob)
    age_preds = age_net.forward()
    age = AGE_GROUPS[age_preds[0].argmax()]
    
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
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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

    kmeans = KMeans(n_clusters=k)
    kmeans.fit(img_array)
    colors = kmeans.cluster_centers_.astype(int)

    # Show colors
    plt.figure(figsize=(6, 2))
    plt.title("Dominant Colors")
    plt.axis("off")
    plt.imshow([colors] * 10)
    plt.show()
    
    return colors

# =============================
# 📌 Main function
def main():
    # ✅ Set image paths (update if necessary)
    IMG_DIR = r"C:/Users/marwe/OneDrive/Bureau/cour S2/tatouage et biiometrie/TP1/Images/"
    img1_path = os.path.join(IMG_DIR, "test1.jpg")
    img2_path = os.path.join(IMG_DIR, "test2.jpg")

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

    # ✅ Step 3: Extract Dominant Colors
    print("🔹 Extracting dominant colors in Image 1...")
    colors_img1 = extract_dominant_color(img1_path)

    print("🔹 Extracting dominant colors in Image 2...")
    colors_img2 = extract_dominant_color(img2_path)

if __name__ == "__main__":
    main()
