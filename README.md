# BannerGeneration

Author: Shanky Ram, Last Updated: Sep 27, 2024

Demo Name: Notebook_Automated_Banner_Generation

Nature of Demo: Vertex AI Enterprise Colab

1.	Download a copy of [MASTER-Colab-Ent]_Notebook_Automated_Banner_Generation

2.	In your GCP project, navigate to Colab Enterprise. Upload your downloaded colab file

3.	Edit in your copy to configure your project details for the following.

PROJECT_ID = "genai-e2e-demos" # @param {type:"string"}
PROJECT_LOCATION = "us-central1" # @param {type:"string"}

4.	Identify your Project Number. You will typically find it in the link

a.	https://console.cloud.google.com/welcome?hl=en&project=<your project ID>
b.	Copy the Project Number, mine is 554686566379

5.	Create two GCS bucket following 
a.	this format - “<Project Number>_telecom_demo_artefacts_bannergen_input
b.	this format - “<Project Number>_telecom_demo_artefacts_bannergen_runtime
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

11.	Refer to the internal demo video for execution steps
