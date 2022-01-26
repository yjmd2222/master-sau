
import os
import cv2
import numpy as np
from sklearn.metrics import average_precision_score
from matplotlib import pyplot as plt

from models import LabelSet, Image, GridLabelSet, GridLabel

# base folders
INPUT_BASE_FOLDER = '../../data/validation/'
CROPPED_BASE_FOLDER = '../../data-cropped/validation/'
PARTITION_BASE_FOLDER = '../../data-partitioned/validation/'
CROPPED_PARTITION_BASE_FOLDER = '../../data-cropped-partition/validation/'

# base folder structure
RGB_FOLDER = 'images/'
IR_FOLDER = 'ir/'
LABEL_FOLDER = 'labels/'

# probably found in a validation run
PREDICTION_FOLDER = '../../predictions_combined/partitioned_rgb_01/'



def get_metrics(fileroot:str, partition_coordinates:'tuple[int, int]'=None, use_ir:bool=False, show_image:bool=False, show_print:bool=False):
    '''@param filename The filename without the filetype/ending. E.g. `2021_09_holtan_0535`'''

     #####                          #     #                                     
    #     # #    #  ####  #    #    ##   ## ###### ##### #####  #  ####   ####  
    #       #    # #    # #    #    # # # # #        #   #    # # #    # #      
     #####  ###### #    # #    #    #  #  # #####    #   #    # # #       ####  
          # #    # #    # # ## #    #     # #        #   #####  # #           # 
    #     # #    # #    # ##  ##    #     # #        #   #   #  # #    # #    # 
     #####  #    #  ####  #    #    #     # ######   #   #    # #  ####   ####  

    if show_print:
        print(f"\nCalculating metrics for {fileroot}")

    base_folder = CROPPED_BASE_FOLDER if use_ir else INPUT_BASE_FOLDER
    if(partition_coordinates is not None):
        base_folder = PARTITION_BASE_FOLDER
        fileroot = f"{fileroot}_p{partition_coordinates[0]}{partition_coordinates[1]}"

    ground_truth_label_set = LabelSet.loadFromFilePath(base_folder + LABEL_FOLDER + fileroot + ".txt", is_cropped=use_ir, partition_coordinates=partition_coordinates)
    ground_truth_grid_label_set = GridLabelSet.from_label_set(ground_truth_label_set)

    prediction_label_set = LabelSet.loadFromFilePath(PREDICTION_FOLDER + fileroot + ".txt", is_cropped=use_ir, partition_coordinates=partition_coordinates)
    prediction_grid_label_set = GridLabelSet.from_label_set(prediction_label_set, is_prediction=True)

    (tp, tn, fp, fn, total_sheep_count, found_sheep_count) = ground_truth_grid_label_set.compare(prediction_grid_label_set)
    
    precision = tp / (tp + fp) if tp > 0 else 0
    recall = tp / (tp + fn) if tp > 0 else 0

    sheep_recall = found_sheep_count / total_sheep_count

    ground_truth = np.concatenate([np.ones(tp), np.ones(fn), np.zeros(tn), np.zeros(fp)])
    predictions =  np.concatenate([np.ones(tp), np.zeros(fn), np.zeros(tn), np.ones(fp)])
    # This is the one Kari used in her metrics
    sklearn_aps = average_precision_score(ground_truth, predictions)

    if show_print:
        print("GRID METRICS")
        print("sklearn_aps:", sklearn_aps)
        print("precision:", precision)
        print("recall:", recall)
        print("sheep_recall:", sheep_recall)
        print("true_positive_count:", tp)
        print("true_negative_count:", tn)
        print("false_postive_count:", fp)
        print("false_negative_count:", fn)


     #####                           #                            
    #     # #    #  ####  #    #     # #    #   ##    ####  ###### 
    #       #    # #    # #    #     # ##  ##  #  #  #    # #      
     #####  ###### #    # #    #     # # ## # #    # #      #####  
          # #    # #    # # ## #     # #    # ###### #  ### #      
    #     # #    # #    # ##  ##     # #    # #    # #    # #      
     #####  #    #  ####  #    #     # #    # #    #  ####  ###### 
    

    if(show_image and ground_truth_label_set.should_show(prediction_label_set)):
        log_string = f"Showing image {fileroot}, {'with' if use_ir else 'without'} IR."
        if(partition_coordinates is not None):
            log_string += f" Partition: {partition_coordinates}."
        print(log_string)

        rgb_image = Image.loadFromImagePath(base_folder + RGB_FOLDER + fileroot + ".JPG", is_cropped=use_ir, partition_coordinates=partition_coordinates)
        if(use_ir):
            ir_image = Image.loadFromImagePath(base_folder + IR_FOLDER + fileroot + ".JPG", is_cropped=use_ir, partition_coordinates=partition_coordinates)

        plt.figure()
        plt.title(fileroot)

        base_image = cv2.cvtColor(rgb_image.img, cv2.COLOR_BGR2RGB)

        if(use_ir):
            base_image = cv2.cvtColor(np.maximum(rgb_image.img, ir_image.img), cv2.COLOR_BGR2RGB)


        # GROUND TRUTH
        ground_truth_image = base_image.copy()

        for ix, iy in np.ndindex(ground_truth_grid_label_set.grid.shape):
            grid_label:GridLabel = ground_truth_grid_label_set.grid[ix, iy]
            ((x_min, x_max), (y_min, y_max)) = grid_label.bounding_box
            bgr_color = (0,255,0) if grid_label.value == True else ((0,0,255) if grid_label.value == None else (150,150,150))
            ground_truth_image = cv2.rectangle(ground_truth_image, (x_min, y_min), (x_max, y_max), bgr_color, -1)

        ground_truth_image = cv2.addWeighted(base_image, 0.9, ground_truth_image, 0.1, 0)

        for label in ground_truth_label_set.labels:
            ground_truth_image = cv2.rectangle(ground_truth_image, (label.left, label.top), (label.right, label.bottom), (0,0,255), 2)

        plt.subplot(2, 2, 1) if use_ir else plt.subplot(1, 2, 1)
        plt.gca().set_title('Ground truth - ' + fileroot)
        plt.imshow(ground_truth_image)


        # PREDICTIONS
        prediction_image = base_image.copy()

        for ix, iy in np.ndindex(prediction_grid_label_set.grid.shape):
            grid_label:GridLabel = prediction_grid_label_set.grid[ix, iy]
            ((x_min, x_max), (y_min, y_max)) = grid_label.bounding_box
            bgr_color = (0,255,0) if grid_label.value == True else ((255,0,0) if grid_label.value == None else (150,150,150))
            prediction_image = cv2.rectangle(prediction_image, (x_min, y_min), (x_max, y_max), bgr_color, -1)

        prediction_image = cv2.addWeighted(base_image, 0.9, prediction_image, 0.1, 0)

        for label in prediction_label_set.labels:
            prediction_image = cv2.rectangle(prediction_image, (label.left, label.top), (label.right, label.bottom), (255,0,0), 2)
            if(label.confidence < 1): # label.confidence is 1 if it's a ground truth. predictions never reach 1.0
                prediction_image = cv2.putText(prediction_image, str(label.confidence), (label.left, label.top - 12), cv2.FONT_HERSHEY_PLAIN, 2, (255,0,0), 2, cv2.LINE_AA)


        plt.subplot(2, 2, 2) if use_ir else plt.subplot(1, 2, 2)
        plt.gca().set_title('Predictions')
        plt.imshow(prediction_image)

        if(use_ir):
            plt.subplot(2, 2, 3)
            plt.gca().set_title('IR')
            plt.imshow(cv2.cvtColor(ir_image.img, cv2.COLOR_BGR2RGB))

        plt.get_current_fig_manager().full_screen_toggle()
        plt.tight_layout()
        plt.show()

    return sklearn_aps, total_sheep_count, found_sheep_count, precision, recall

def calculate_metrics(partition_coordinates:'tuple[int, int]'=None, use_ir:bool=False, show_image:bool=False, show_print:bool=False):
    aps_list = []
    precision_list = []
    recall_list = []
    total_sheep_count_sum = 0
    found_sheep_count_sum = 0

    filenames = os.listdir(PREDICTION_FOLDER)
    filenames.sort()
    for filename in filenames:
        fileroot = filename.split('.')[0]
        aps, total_sheep_count, found_sheep_count, precision, recall = get_metrics(fileroot, partition_coordinates, use_ir, show_image, show_print)
        aps_list.append(aps)
        precision_list.append(precision)
        recall_list.append(recall)
        total_sheep_count_sum += total_sheep_count
        found_sheep_count_sum += found_sheep_count

    print("GRID METRICS")
    print("AP:", sum(aps_list) / len(aps_list))
    print("Precision:", sum(precision_list) / len(precision_list))
    print("Recall:", sum(recall_list) / len(recall_list))
    print("Sheep recall:", found_sheep_count_sum / total_sheep_count_sum)
    return aps_list, precision_list, recall_list, total_sheep_count_sum, found_sheep_count_sum

def calculate_metrics_for_confidences():
    # get_metrics("2019_08_storli1_0720", partition_coordinates=None, use_ir=False, show_image=True)
    confidences = [0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    # confidences = [0.5, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, 0.675, 0.7,]
    conf_ap = []
    conf_precision = []
    conf_recall = []
    conf_sheep_recall = []

    for conf in confidences:
        LabelSet.label_confidence_threshold = conf
        print("\nThreshold for label confidence:", LabelSet.label_confidence_threshold)

        aps_list, precision_list, recall_list, total_sheep_count_sum, found_sheep_count_sum = calculate_metrics()
        conf_ap.append(sum(aps_list) / len(aps_list))
        conf_precision.append(sum(precision_list) / len(precision_list))
        conf_recall.append(sum(recall_list) / len(recall_list))
        conf_sheep_recall.append(found_sheep_count_sum / total_sheep_count_sum)

    plt.plot(confidences, conf_ap, label="ap")
    plt.plot(confidences, conf_precision, label="precision")
    plt.plot(confidences, conf_recall, label="recall")
    plt.plot(confidences, conf_sheep_recall, label="sheep_recall")
    plt.legend()
    plt.show()



if __name__ == "__main__":
    # calculate_metrics_for_confidences()

    calculate_metrics(partition_coordinates=None, use_ir=False, show_image=True, show_print=True)

