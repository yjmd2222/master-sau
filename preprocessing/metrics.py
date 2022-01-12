
import cv2
import numpy as np
from sklearn.metrics import average_precision_score
from matplotlib import pyplot as plt

from models import LabelSet, Image, GridLabelSet, GridLabel

# base folders
INPUT_BASE_FOLDER = '../data/'
CROPPED_BASE_FOLDER = '../data-cropped/'
PARTITION_BASE_FOLDER = '../data-partitioned/'

# base folder structure
RGB_FOLDER = 'rgb/'
IR_FOLDER = 'ir/'
LABEL_FOLDER = 'labels/'
PREDICTION_FOLDER = 'predictions/'



def show_metrics(fileroot:str, partition_coordinates:'tuple[int, int]'=None, use_ir:bool=False, show_image:bool=False):
    '''@param filename The filename without the filetype/ending. E.g. `2021_09_holtan_0535`'''

     #####                          #     #                                     
    #     # #    #  ####  #    #    ##   ## ###### ##### #####  #  ####   ####  
    #       #    # #    # #    #    # # # # #        #   #    # # #    # #      
     #####  ###### #    # #    #    #  #  # #####    #   #    # # #       ####  
          # #    # #    # # ## #    #     # #        #   #####  # #           # 
    #     # #    # #    # ##  ##    #     # #        #   #   #  # #    # #    # 
     #####  #    #  ####  #    #    #     # ######   #   #    # #  ####   ####  
                                                                             
    print(f"Showing metrics for {fileroot}")

    base_folder = CROPPED_BASE_FOLDER if use_ir else INPUT_BASE_FOLDER
    if(partition_coordinates is not None):
        base_folder = PARTITION_BASE_FOLDER
        fileroot = f"{fileroot}_p{partition_coordinates[0]}{partition_coordinates[1]}"

    ground_truth_label_set = LabelSet.loadFromFilePath(base_folder + LABEL_FOLDER + fileroot + ".txt", is_cropped=use_ir, partition_coordinates=partition_coordinates)
    ground_truth_grid_label_set = GridLabelSet.from_label_set(ground_truth_label_set)

    prediction_label_set = LabelSet.loadFromFilePath(base_folder + PREDICTION_FOLDER + fileroot + ".txt", is_cropped=use_ir, partition_coordinates=partition_coordinates)
    prediction_grid_label_set = GridLabelSet.from_label_set(prediction_label_set, is_prediction=True)

    (tp, tn, fp, fn) = ground_truth_grid_label_set.compare(prediction_grid_label_set)
    
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)

    ground_truth = np.concatenate([np.ones(tp), np.ones(fn), np.zeros(tn), np.zeros(fp)])
    predictions =  np.concatenate([np.ones(tp), np.zeros(fn), np.zeros(tn), np.ones(fp)])
    # This is the one Kari used in her metrics
    sklearn_aps = average_precision_score(ground_truth, predictions)

    print("sklearn_aps:", sklearn_aps)
    print("precision:", precision)
    print("recall:", recall)
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
                                                               

    if(show_image):
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
            bgr_color = (0,255,0) if grid_label.value == True else ((255,0,0) if grid_label.value == None else (150,150,150))
            ground_truth_image = cv2.rectangle(ground_truth_image, (x_min, y_min), (x_max, y_max), bgr_color, -1)

        ground_truth_image = cv2.addWeighted(base_image, 0.6, ground_truth_image, 0.4, 0)

        for label in ground_truth_label_set.labels:
            ground_truth_image = cv2.rectangle(ground_truth_image, (label.left, label.top), (label.right, label.bottom), (0,0,255), 2)

        plt.subplot(1, 2, 1)
        plt.gca().set_title('Ground truth')
        plt.imshow(cv2.cvtColor(ground_truth_image, cv2.COLOR_BGR2RGB))


        # PREDICTIONS
        prediction_image = base_image.copy()

        for ix, iy in np.ndindex(prediction_grid_label_set.grid.shape):
            grid_label:GridLabel = prediction_grid_label_set.grid[ix, iy]
            ((x_min, x_max), (y_min, y_max)) = grid_label.bounding_box
            bgr_color = (0,255,0) if grid_label.value == True else ((255,0,0) if grid_label.value == None else (150,150,150))
            prediction_image = cv2.rectangle(prediction_image, (x_min, y_min), (x_max, y_max), bgr_color, -1)

        prediction_image = cv2.addWeighted(base_image, 0.6, prediction_image, 0.4, 0)

        for label in prediction_label_set.labels:
            prediction_image = cv2.rectangle(prediction_image, (label.left, label.top), (label.right, label.bottom), (0,0,255), 2)


        plt.subplot(1, 2, 2)
        plt.gca().set_title('Predictions')
        plt.imshow(cv2.cvtColor(prediction_image, cv2.COLOR_BGR2RGB))

        # plt.get_current_fig_manager().full_screen_toggle()
        plt.show()




if __name__ == "__main__":
    show_metrics("2019_08_storli1_0720", partition_coordinates=None, use_ir=False, show_image=True)

        