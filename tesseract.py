def readStream(inputimage):
    import cv2
    import os, argparse
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    images = cv2.imread(inputimage)

    #convert to grayscale image
    gray = cv2.cvtColor(images, cv2.COLOR_BGR2GRAY)
    results = pytesseract.image_to_data(gray,
                                        output_type=pytesseract.Output.DICT)
    res = []
    # Then loop over each of the individual text
    # localizations
    for i in range(0, len(results["text"])):

        # We can then extract the bounding box coordinates
        # of the text region from  the current result
        x = results["left"][i]
        y = results["top"][i]
        w = results["width"][i]
        h = results["height"][i]

        # We will also extract the OCR text itself along
        # with the confidence of the text localization
        text = results["text"][i]
        conf = float(results["conf"][i])
        # filter out weak confidence text localizations
        if conf > 90:
            # We will display the confidence and text to
            # our terminal
            res.append(text.lower())

            # We then strip out non-ASCII text so we can
            # draw the text on the image We will be using
            # OpenCV, then draw a bounding box around the
            # text along with the text itself
            text = "".join(text).strip()
            cv2.rectangle(images, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(images, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (0, 255, 255), 3)
    cv2.imshow("Image", images)
    cv2.waitKey(0)
    return res
