from google.cloud import vision
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"

def detect_text(path):
    client = vision.ImageAnnotatorClient()
    with open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')
    for text in texts:
        print('\n"{}"'.format(text.description))
        vertices = [f'({vertex.x},{vertex.y})' for vertex in text.bounding_poly.vertices]
        print('bounds: {}'.format(','.join(vertices)))
    if response.error.message:
        raise Exception(f'{response.error.message}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors')

def detect_handwriting(path):
    """Detects handwriting in the file."""
    client = vision.ImageAnnotatorClient()

    with open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)  # Use document_text_detection for handwriting
    texts = response.text_annotations

    print('Detected Text:')

    for text in texts:
        print('\n"{}"'.format(text.description))
        
        # Optional: print the bounds of the detected text
        vertices = ['({},{})'.format(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        print('Bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception('{}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors'.format(response.error.message))


# detect_handwriting('PATH_TO_YOUR_IMAGE')

detect_text('./image.png')