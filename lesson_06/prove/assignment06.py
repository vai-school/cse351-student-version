"""
Course: CSE 351
Assignment: 06
Author: Robert Vaile

Instructions:

- see instructions in the assignment description in Canvas

""" 

import multiprocessing as mp
import os
import cv2
import numpy as np

from cse351 import *

# Folders
INPUT_FOLDER = "faces"
STEP1_OUTPUT_FOLDER = "step1_smoothed"
STEP2_OUTPUT_FOLDER = "step2_grayscale"
STEP3_OUTPUT_FOLDER = "step3_edges"

# Parameters for image processing
GAUSSIAN_BLUR_KERNEL_SIZE = (5, 5)
CANNY_THRESHOLD1 = 75
CANNY_THRESHOLD2 = 155

# Allowed image extensions
ALLOWED_EXTENSIONS = ['.jpg']

# ---------------------------------------------------------------------------
def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")

# ---------------------------------------------------------------------------
def task_convert_to_grayscale(image):
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        return image # Already grayscale
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# ---------------------------------------------------------------------------
def task_smooth_image(image, kernel_size):
    return cv2.GaussianBlur(image, kernel_size, 0)

# ---------------------------------------------------------------------------
def task_detect_edges(image, threshold1, threshold2):
    if len(image.shape) == 3 and image.shape[2] == 3:
        print("Warning: Applying Canny to a 3-channel image. Converting to grayscale first for Canny.")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] != 1 : # Should not happen with typical images
        print(f"Warning: Input image for Canny has an unexpected number of channels: {image.shape[2]}")
        return image # Or raise error
    return cv2.Canny(image, threshold1, threshold2)

# ---------------------------------------------------------------------------
def process_images_in_folder(input_folder,              # input folder with images
                             output_folder,             # output folder for processed images
                             processing_function,       # function to process the image (ie., task_...())
                             load_args=None,            # Optional args for cv2.imread
                             processing_args=None):     # Optional args for processing function

    create_folder_if_not_exists(output_folder)
    print(f"\nProcessing images from '{input_folder}' to '{output_folder}'...")

    processed_count = 0
    for filename in os.listdir(input_folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue

        input_image_path = os.path.join(input_folder, filename)
        output_image_path = os.path.join(output_folder, filename) # Keep original filename

        try:
            # Read the image
            if load_args is not None:
                img = cv2.imread(input_image_path, load_args)
            else:
                img = cv2.imread(input_image_path)

            if img is None:
                print(f"Warning: Could not read image '{input_image_path}'. Skipping.")
                continue

            # Apply the processing function
            if processing_args:
                processed_img = processing_function(img, *processing_args)
            else:
                processed_img = processing_function(img)

            # Save the processed image
            cv2.imwrite(output_image_path, processed_img)

            processed_count += 1
        except Exception as e:
            print(f"Error processing file '{input_image_path}': {e}")

    print(f"Finished processing. {processed_count} images processed into '{output_folder}'.")

# ---------------------------------------------------------------------------
def run_image_processing_pipeline():
    create_folder_if_not_exists(STEP3_OUTPUT_FOLDER)

    q1 = mp.Queue()
    q2 = mp.Queue()
    q3 = mp.Queue()

    print("Starting image processing pipeline...")
    smooth_processes = []
    grayscale_processes = []
    edge_processes = []


    for i in range(2):
        p = mp.Process(target=smooth_worker, args=(q1, q2))
        p.start()
        smooth_processes.append(p)
    
    for i in range(2):
        p = mp.Process(target=grayscale_worker, args=(q2, q3))
        p.start()
        grayscale_processes.append(p)

    for i in range(2):
        p = mp.Process(target=edge_worker, args=(q3,))
        p.start()
        edge_processes.append(p)

    for filename in os.listdir(INPUT_FOLDER):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue
        input_path = os.path.join(INPUT_FOLDER, filename)
        q1.put(input_path)

    for p in smooth_processes:
        q1.put("Done")

    for p in smooth_processes:
        p.join()

    for p in grayscale_processes:
        q2.put("Done")

    for p in grayscale_processes:
        p.join()
    
    for p in edge_processes:
        q3.put("Done")

    for p in edge_processes:
        p.join()


def smooth_worker(q1, q2):
    while True:
        filename = q1.get()
        if filename == "Done":
            break

        img = cv2.imread(filename)
        smoothed = task_smooth_image(img, GAUSSIAN_BLUR_KERNEL_SIZE)
        q2.put((filename, smoothed))

def grayscale_worker(q2,q3):
    while True:
        item = q2.get()
        if item == "Done":
            break
        filename, smoothed = item
        grayscale = task_convert_to_grayscale(smoothed)
        q3.put((filename, grayscale))

def edge_worker(q3):
    while True:
        item = q3.get()
        if item == "Done":
            break
        filename, grayscale = item
        output_image_path = os.path.join(STEP3_OUTPUT_FOLDER, os.path.basename(filename))
        edge = task_detect_edges(grayscale, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        cv2.imwrite(output_image_path, edge)



# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log = Log(show_terminal=True)
    log.start_timer('Processing Images')

    # check for input folder
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The input folder '{INPUT_FOLDER}' was not found.")
        print(f"Create it and place your face images inside it.")
        print('Link to faces.zip:')
        print('   https://drive.google.com/file/d/1eebhLE51axpLZoU6s_Shtw1QNcXqtyHM/view?usp=sharing')
    else:
        run_image_processing_pipeline()

    log.write()
    log.stop_timer('Total Time To complete')
