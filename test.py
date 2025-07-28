import cv2
import numpy as np

# Read the image
image_path = "D:\Cosumar\ocr_pages\page_1.png"
img_rgb = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

if img_rgb is not None:
    print(f"Image loaded successfully! Shape: {img_rgb.shape}")
else:
    print("Error: Could not read the image") 

print(f"{cv2.COLOR_RGB2GRAY}")

gray_img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
_, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
cv2.imwrite("output_grayscale.png", gray_img)
cv2.imwrite("output_binary.png", binary_img)

h = img_rgb.shape[0]
w = img_rgb.shape[1]

differences = []
for row in range(h):
    for col in range(w):
        pixel_binary = binary_img[row, col]
        pixel_gray = gray_img[row, col]
        if pixel_binary != pixel_gray:
            differences.append((row, col, pixel_binary, pixel_gray))

print(differences)
print(f"Number of differences found: {len(differences)}") 
print(f"Image dimensions: {h*w}")
print(f"Rate of differences: {len(differences) / (h * w) * 100:.2f}%")
