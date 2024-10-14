import cv2
import easyocr

def bypass_captcha_easyocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_REPLICATE)
    
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    letter_image_regions = sorted([cv2.boundingRect(contour) for contour in contours], key=lambda x: x[0])

    reader = easyocr.Reader(['en'], gpu=True)
    predictions = []

    for x, y, w, h in letter_image_regions:
        if w * h < 100:
            continue

        if y-2 < 0 or x-2 < 0 or (y + h + 2) > gray.shape[0] or (x + w + 2) > gray.shape[1]:
            continue

        letter_image = gray[y-2:y+h+2, x-2:x+w+2]
        
        if letter_image.size == 0:
            continue
        
        letter_image_resized = cv2.resize(letter_image, (50, 50))
        
        result = reader.readtext(letter_image_resized, paragraph=False, low_text=0.3, contrast_ths=0.5)
        
        if result and len(result) > 0:
            predictions.append(result[0][1].strip().upper())

    final_text = ''.join(predictions)
    return final_text

def image_process():
    for i in range(1, 34):
        print(i)
        image = cv2.imread(f"ssThread-{i}.png")  # Load your image file
        captcha_easyocr = bypass_captcha_easyocr(image)
        print(f"Captcha result: {captcha_easyocr}")

if __name__ == "__main__":
    print("Running script...")
    image_process()
