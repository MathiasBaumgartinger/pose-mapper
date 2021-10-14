# Pose-Mapper

A Blender-Python plugin and the required preprocessing for mapping pose-estimated data onto a generic model. The current version uses a model exported from !(Makehuman)[http://www.makehumancommunity.org/] in the Makehuman 2 standard (``.mhx``). The plugin offers the application of multiple video-sequences one by one onto the same model. For instance motions over the course of a cutscene can be mapped. The scene has to be manually cut in before.

## Usage

The workflow currently includes 4 major steps:
1. Finding an (appropriate) video-sequence
2. Preprocessing
3. Exporting and loading a model from Makehuman
4. Application on the model

### Prerequisites

- mediapipe >= 0.8.4.2
- opencv >= 4.0.1
- MHX2 plugin for blender (http://www.makehumancommunity.org/content/plugins.html)

### Step 1: Finding an (appropriate) video-sequence

In the current state, finding an appropriate video sequence is quite challenging. There are certain factors that have a major impact on the accuracy of the pose tracker. The main criteria I found to achieve good results are:
- Only one person on screen
The pose-tracker can only track one person at a time - with multiple persons it will mix them up frequently and thus produce heavy inaccuracies
- Camera movement
Optimally the camera should not move at all, as any movement on the camera will be mapped to the model
- High resolutions
I have noticed that the higher the resolution of the video, the higher the output quality
- Full shots
The more of the body is visible the less has to predicted by magic.
- Contrast between person and background
A high contrast makes finding movement for the predictor a lot easier

### Step 2: Preprocessing 

Preprocessing in the case of this repository describes the process of creating a JSON with positions of landmarks (as described in (here)[https://google.github.io/mediapipe/images/mobile/pose_tracking_full_body_landmarks.png]) frame by frame. The preprocessing used here is based on the ![MediaPipe Pose-Detection](https://google.github.io/mediapipe/solutions/pose.html).

Usage: ``python ./preprocess/mp_pose_preprocess.py <path_to_video> <destination_file>``

### Step 3: Exporting and loading a model from Makehuman

Exporting the desired model from Makehuman as ``.mhx2`` file and loading the model into blender using the MHX2 plugin described in the prerequisites (http://www.makehumancommunity.org/content/plugins.html). A generic model from Makehuman is inside the directory ``models/standard.mhx2``. The application can be applied on any model of the ``.mhx2`` standard, just make sure to assign the name of the model inside of blender to ``MODEL_NAME``.


### Step 4a: Application on the model

With a correct setup, from here one just needs to open the ``pose-application.py`` in blender, tune the constants accordingly (more information under Configuration) and run the script. The results can be best obtained in the "Animation" tab of Blender. 

### Step 4b: Visualizing with "plain.py"

Another visualization of the data is provided by means of the plain-object. With it only the landmarks are being depicted according to the pose-estimator inside of blender without a matching model. Step 4a and 3 are not necessary for this visualization. I recommend not to use a plain and a model inside the same blender execution as it causes bugs.

## Configuration

### pose_application
- ``PATH_PREFIX``
    - ``importlib.util`` sadly did not work with relative paths for me so you have to define the root to the location of this git repo on your local machine
    - E.g.: ``"C:/sem2/P1/implementations/pose-estimation/"``
- ``MODEL_NAME``
    - The model name as depicted in Blender in the scene-collection
- ``DATA_PATHS`` 
    - Give the path to any number of preprocessed jsons in here. A new json will be handled as "cut".
    - E.g.: [PATH_PREFIX + "preprocess/output/walking.json", PATH_PREFIX + "preprocess/output/sit_down_fixed.json"]
- ``DISTANCE_FACTOR``
    - How much the location of the screen space (0-1) of model in the pose estimator is being multiplied with 
- ``AVG_OVER_N_FRAMES``
    - How many frames should be averaged (applying each estimated frame makes it very jittery)
- ``FRAMES_BETWEEN``
    - How many keyframes blender should put between the i-th video
- ``CONNECTIONS``
    - How the PoseBones in Blender should be connected, it might be necessary to change this if one uses another estimator/model, otherwise i suggest leaving this the way it is

### preprocess
- ``BODY_PARTS``
    - Defines which way to name the bones identified by 0 to 32 from https://google.github.io/mediapipe/images/mobile/pose_tracking_full_body_landmarks.png. It should match the ``CONNECTIONS`` from the pose-application as well as the model's according bones

## Limitations

- Jittering
As of now the mapping is very jittery. Increasing ``AVG_OVER_N_FRAMES`` makes this better, leads to other bugs in some cases however.
- No "real-life" body constraints
Sometimes body-parts are overlapping/pointing in directions which are actually not possible
- Only one person
As mentioned before only one person can be tracked
- Camera perspectives
Camera perspectives might distort the way the pose-estimator estimates the coordinates
- Camera movement
Camera movement appears as model movement in the end, the model would need to be focussed in the middle
- Translation calculated hard-coded
The translation is as of now hardcoded with ``DISTANCE_FACTOR``
- Cuts have to be marked manually
If the video has a cutscene, the scene must be manually cut and then individually preprocessed
- Only arms and legs
Only arms and legs are being tracked at the moment. It would be further possible to track fingers/head/etc..

## Credits

The preprocessing script was heavily influenced by https://www.youtube.com/watch?v=brwgBf6VB0I&t=750s.
All this is based on the mighty work of mediapipe's pose-estimator.
Kudos to the Makehuman community!
