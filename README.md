Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Banner Generation

Author: Shanky Ram, Last Updated: Sep 27, 2024

Demo Name: Notebook_Automated_Banner_Generation

Nature of Demo: Vertex AI Enterprise Colab

1.	Download a copy of [MASTER-Colab-Ent]_Notebook_Automated_Banner_Generation

2.	In your GCP project, navigate to Colab Enterprise. Upload your downloaded colab file

3.	Edit in your copy to configure your project details for the following.

PROJECT_ID = "genai-e2e-demos" # @param {type:"string"}
PROJECT_LOCATION = "us-central1" # @param {type:"string"}

4.	Identify your Project Number. Copy the Project Number, mine is 554686566379

5.	Create two GCS bucket following 
a.	this format - <ProjectNumber>_telecom_demo_artefacts_bannergen_input
b.	this format - <ProjectNumber>_telecom_demo_artefacts_bannergen_runtime
c.	In the above example this is - 554686566379_telecom_demo_artefacts_bannergen_input

6.	Down the entire “Artefacts” and 
a.	upload them into the “ bucket
b.	Take note to upload the entire “Artefacts” folder as shown below

7.	Create a new Firestore instance “banner-gen-app” in Native mode with Database ID “banner-gen-app”

8.	In Argolis Colab, create your runtime template and runtime
a.	Pre-requisite - 
i.	Ensure the following APIs are enabled: Vertex AI, Compute Engine & Dataform. This is a colab pre-requisite
ii.	Ensure you have a VPC subnet with Google Private Service Connect enabled on the subnet 
iii.	Alternatively ensure your project supports external IPs for GCE VMs
b.	Create the runtime template in Colab Enterprise, with option “Secure Boot” and correct VPC subnet
c.	Create a runtime using the previously created runtime template

9.	In notebook choose “Connect to Runtime” > “Connect to Existing Runtime”

10.	Run the notebook, read the demo execution step in About Demo

# Execution Steps
Section - CoLab Description

Author - shankyram@

Contributor Attribution
This code uses prompts designed by kkrish
Thanks to PSO team members gopalad dsharmila for pointing me to open cv, rembg libraries

Last Updated On - 31 Oct 2024

Solution to demonstrate a banner generation pipeline with
Imagen3 for actor asset creation
Python & Gradio frontend to
   * Imagen3 generated actor assets for target segments
   * Pipeline action to remove actor asset background for overlay placement
   * UI for design banner layout & multi text or image design placement
   * UI for campaign definition for auto banner creation
Leveraging libraries like pillow, cv2, rembg, SAM & Imagen models

Introduction
This demo showcases a cutting-edge solution for hyper-personalized banner generation, designed to revolutionize your telecom Customer Value Management (CVM) strategies. By leveraging AI and a dynamic approach, we can create highly targeted and engaging banners that resonate with individual customer segments, driving conversions and enhancing brand loyalty.
The Problem: Traditional banner campaigns often rely on generic messaging and visuals, resulting in low engagement and limited impact. Customers are bombarded with irrelevant ads, leading to banner blindness and missed opportunities.
Our Solution: This innovative platform utilizes AI-powered image generation and dynamic banner assembly to create hyper-personalized experiences. Imagine banners that feature:
Contexual faces: Actors that reflect the age, ethnicity, and lifestyle of specific customer segments.
Personalized offers: Product recommendations and promotions tailored to individual needs and preferences.
Dynamic backgrounds: Visually appealing scenes that resonate with customer interests and demographics.

Setup Instructions

1. Create two GCS bucket following
  this format - “<Project Number>_telecom_demo_artefacts_bannergen_input
  this format - “<Project Number>_telecom_demo_artefacts_bannergen_runtime
  In the above example this is - 554686566379_telecom_demo_artefacts_bannergen_input

  Down the entire “Artefacts” and
  upload them into the “ bucket
  Take note to upload the entire “Artefacts” folder as shown below

2. Create a new Firestore instance “banner-gen-app” in Native mode with Database ID “banner-gen-app”

3. If you need to update new banner templates, or logos etc, update into the bucket directory "*telecom_demo_artefacts_bannergen_input - /Logo" or /Background or /Actors (to bring your own talent images)"
4. Please ensure there is nothing uploaded in "_telecom_demo_artefacts_bannergen_input/Background_Processed" since this will automatically be done in notebook code
5. If you add new assets into "_telecom_demo_artefacts_bannergen_input" in "Actors" / "Background", "Graphics", "Logo", ensure that you rerun the colab from Section - Demo Configuration & Initialization
6. The contents of "_telecom_demo_artefacts_bannergen_input/Config" are for bootstrapping only and subsequently are updated into the firebase DB

7. Note that all output images generated are temporarily retained in colab local dir and will NOT be saved on colab termination. If you want to reuse them, download them from the folder /content/demo/output for future reference.

Execution Instructions

Step 1: Demo Asset Library
Explore the building blocks of dynamic banners, including a diverse library of actors, backgrounds, logos, graphics, and text elements.
Remember to click on the check box in file explorer not the arrow since the UX components seem to have a better experience with checkbox

Step 2: Demo Asset Creation
Witness the creation of new visual segments aligned with your specific customer targeting needs.
See how AI-powered image generation (Imagen3) can be used to create realistic and diverse actors.
Remember to save the images to the library for the visual segment to be saved in database and images to be available for banner generation

Step 3: Demo Asset Preprocessing
Understand the importance of background removal for seamless integration of actors and elements onto banner templates.
Remember to preprocess newly created visual assets for removing background
Remember logos and graphic elements are expected to be already having transparent background

Step 4: Demo Banner Template Configuration
Learn how banner templates can be defined using intuitive UX providing flexibility and creative control.
Remember that this is configuration controlling placement of text and images in output. Use the tool selection options to define where text header / body and various graphic elements need to be placed

Step 5: Demo Banner Generation
Experience the magic of dynamic banner generation, where personalized banners are automatically created for multiple templates and visual segments.
Remember to click on refresh visual segment to reload the dropdown for reflecting new visual segments

Code Updates
31 Oct 2024
 - Added fix to support new banner templates to be loaded via upload to GCS bucket (see setup instruction 3 above)
 - Added fix to refresh visual segment
 - Added fix to leave some of image / text inputs in banner generation empty
    
