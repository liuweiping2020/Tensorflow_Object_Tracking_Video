import os
import cv2
import progressbar
import copy
import utils_image
import Utils_Imagenet
import frame
import multiclass_rectangle
import vid_classes
from PIL import Image
import sys

### Fucntions to mount the video from frames

def make_video_from_list(out_vid_path, frames_list):
	if frames_list[0] is not None:
	    img = cv2.imread(frames_list[0], True)
	    print frames_list[0]
	    h, w = img.shape[:2]
	    fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
	    out = cv2.VideoWriter(out_vid_path,fourcc, 20.0, (w, h), True)
	    print("Start Making File Video:%s " % out_vid_path)
	    print("%d Frames to Compress"%len(frames_list))
	    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
	    for i in progress(range(0,len(frames_list))):
	        if utils_image.check_image_with_pil(frames_list[i]):
	            out.write(img)
	            img = cv2.imread(frames_list[i], True)
	    out.release()
	    print("Finished Making File Video:%s " % out_vid_path)


def make_video_from_frames(out_vid_path, frames):
	if frames[0] is not None:
	    h, w = frames[0].shape[:2]
	    fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
	    out = cv2.VideoWriter(out_vid_path,fourcc, 20.0, (w, h), True)
	    print("Start Making File Video:%s " % out_vid_path)
	    print("%d Frames to Compress"%len(frames))
	    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
	    for i in progress(range(0,len(frames))):
	        out.write(frames[i])
	    out.release()
	    print("Finished Making File Video:%s " % out_vid_path)


####### FOR TENSORBOX ###########

def extract_idl_from_frames(vid_path, video_perc, path_video_folder, folder_path_frames, idl_filename):
    
    ####### Creating Folder for the video frames and the idl file for the list
    
    if not os.path.exists(path_video_folder):
        os.makedirs(path_video_folder)
        print("Created Folder: %s"%path_video_folder)
    if not os.path.exists(path_video_folder+'/'+folder_path_frames):
        os.makedirs(path_video_folder+'/'+folder_path_frames)
        print("Created Folder: %s"% (path_video_folder+'/'+folder_path_frames))
    if not os.path.exists(idl_filename):
        open(idl_filename, 'a')
        print "Created File: "+ idl_filename
    list=[]
    # Opening & Reading the Video

    print("Opening File Video:%s " % vid_path)
    vidcap = cv2.VideoCapture(vid_path)
    if not vidcap.isOpened():
        print "could Not Open :",vid_path
        return
    print("Opened File Video:%s " % vid_path)
    print("Start Reading File Video:%s " % vid_path)
    
    total = int((vidcap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)/100)*video_perc)
    
    print("%d Frames to Read"%total)
    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
    image = vidcap.read()
    with open(idl_filename, 'w') as f:
        for i in progress(range(0,total)):
            #frame_name="%s/%s/fram%d.jpeg"%(path_video_folder,folder_path_frames,i)
            list.append("%s/%sframe%d.jpeg"%(path_video_folder,folder_path_frames,i))
            cv2.imwrite("%s/%sframe%d.jpeg"%(path_video_folder,folder_path_frames,i), image[1])     # save frame as JPEG file
            image = vidcap.read()

    print("Finish Reading File Video:%s " % vid_path)
    return list

### Function to track objects and spread informations between frames

def track_objects(video_info):

    class_code_string_list= ['n02691156','n02419796','n02131653','n02834778','n01503061','n02924116','n02958343','n02402425','n02084071','n02121808','n02503517','n02118333','n02510455','n02342885','n02374451','n02129165','n01674464','n02484322','n03790512','n02324045','n02509815','n02411705','n01726692','n02355227','n02129604','n04468005','n01662784','n04530566','n02062744','n02391049']

    previous_frame= None
    previous_num_obj=-1

    cropped_img_array=[]
    tracked_video=[]

    for frame_info in video_info:
        print "Tracking Frame Nr: %d"%frame_info.frame
        print len(frame_info.rects)
        current_frame = frame.Frame_Info()
        current_frame=frame_info.duplicate()
        current_frame.rects=[]
        print len(frame_info.rects)
        if previous_frame is not None:
            print "Previous Frame obj:%d"%previous_num_obj
            for rect in frame_info.rects:
                print "Entered into the rect check"
                max_rect=None
                max_iou=0
                current_rect= multiclass_rectangle.Rectangle_Multiclass()
                trackID=-1
                if previous_num_obj >0: ### If i come here means that there's the same number of object between the previous and the current frame
                    print "Entered into the rect check with :%d objects"%previous_num_obj
                    id_rect=0
                    max_id=0
                    for prev_rect in previous_frame.rects:
                        print "Entered"
                        if rect.iou(prev_rect)>max_iou:
                            max_iou=rect.iou(prev_rect)
                            max_rect=prev_rect
                            max_id=id_rect
                        id_rect=id_rect+1
                    print "Lenght previous rects array: %d"%len(previous_frame.rects)
                    print "max_rect track ID: %d"%max_rect.trackID
                    print "max_rect label: %s"%max_rect.label
                    current_rect.load_labeled_rect(max_rect.trackID, max_rect.true_confidence, max_rect.label_confidence, max_rect.x1,max_rect.y1,max_rect.x2 ,max_rect.y2, max_rect.label, max_rect.label, max_rect.label)
                    current_frame.append_labeled_rect(current_rect)
                    rect.load_label(max_rect.trackID,max_rect.label_confidence, max_rect.label, max_rect.label, max_rect.label)
                    previous_frame.rects.pop(max_id)
                    previous_num_obj=previous_num_obj-1
                else:
                    ### If i come here means that there's more objects in the current frame respect to che previous
                    if previous_num_obj == 0:
                        trackID = len(frame_info.rects)
                        previous_num_obj = -1
                    current_rect= multiclass_rectangle.Rectangle_Multiclass()

                    img= Image.open(frame_info.filename)
                    cor = (rect.x1,rect.y1,rect.x2 ,rect.y2)

                    cropped_img=img.crop(cor)
                    cropped_img_name="cropped_frame_%d.JPEG"%(frame_info.frame)
                    cropped_img.save(cropped_img_name)
                    cropped_img_array.append(cropped_img_name)

                    label, confidence = Utils_Imagenet.run_inception_once(cropped_img_name)
                    rect.load_label(trackID,confidence, vid_classes.code_to_class_string(label), class_code_string_list[vid_classes.class_string_to_comp_code(vid_classes.code_to_class_string(label))], label)
                    current_rect.load_labeled_rect(trackID, rect.true_confidence, confidence, rect.x1,rect.y1,rect.x2 ,rect.y2, vid_classes.code_to_class_string(label), class_code_string_list[vid_classes.class_string_to_comp_code(vid_classes.code_to_class_string(label))], label)
                    print "current_rect track ID: %d"%current_rect.trackID
                    print "current_rect label: %s"%current_rect.label
                    current_frame.append_labeled_rect(current_rect)
        else:
            trackID=1

            for rect in frame_info.rects:
                
                current_rect= multiclass_rectangle.Rectangle_Multiclass()

                img= Image.open(frame_info.filename)
                cor = (rect.x1,rect.y1,rect.x2 ,rect.y2)

                cropped_img=img.crop(cor)
                cropped_img_name="cropped_frame_%d.JPEG"%(frame_info.frame)
                cropped_img.save(cropped_img_name)
                cropped_img_array.append(cropped_img_name)

                label, confidence = Utils_Imagenet.run_inception_once(cropped_img_name)
                rect.load_label(trackID,confidence, vid_classes.code_to_class_string(label), class_code_string_list[vid_classes.class_string_to_comp_code(vid_classes.code_to_class_string(label))], label)
                current_rect.load_labeled_rect(trackID, rect.true_confidence, confidence, rect.x1,rect.y1,rect.x2 ,rect.y2, vid_classes.code_to_class_string(label), class_code_string_list[vid_classes.class_string_to_comp_code(vid_classes.code_to_class_string(label))], label)
                current_frame.append_labeled_rect(current_rect)
                
                trackID=trackID+1

        previous_num_obj=len(frame_info.rects)
        previous_frame=frame_info.duplicate()
        previous_frame.duplicate_rects(frame_info.rects)

        print previous_frame
        print "Previous Frame obj:%d"%previous_num_obj
        print "prev_rect 0 track ID: %d"%previous_frame.rects[0].trackID
        print "prev_rect 0 label: %s"%previous_frame.rects[0].label
        tracked_video.insert(len(tracked_video), current_frame)

    return tracked_video


####### FOR YOLO ###########

def extract_frames(vid_path, video_perc):
    list=[]
    frames=[]
    # Opening & Reading the Video
    print("Opening File Video:%s " % vid_path)
    vidcap = cv2.VideoCapture(vid_path)
    if not vidcap.isOpened():
        print "could Not Open :",vid_path
        return
    print("Opened File Video:%s " % vid_path)
    print("Start Reading File Video:%s " % vid_path)
    image = vidcap.read()
    total = int((vidcap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)/100)*video_perc)
    print("%d Frames to Read"%total)
    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
    for i in progress(range(0,total)):
        list.append("frame%d.jpg" % i)
        frames.append(image)
        image = vidcap.read()
    print("Finish Reading File Video:%s " % vid_path)
    return frames, list
