---
title:     "Automating HDR Photo Creation in Adobe Lightroom"
date:      2025-04-02
permalink: /posts/2025/04/automating-hdr-photo-creation-in-adobe-lightroom
tags:
  - automation
  - photography
---

High Dynamic Range (HDR) photography allows photographers to capture a broader range of light and detail than standard photography. While Adobe Lightroom provides tools for HDR merging, the process can be labor-intensive, especially when dealing with numerous images. This article explores an approach to automate HDR photo creation, enhancing efficiency and workflow.

In this blog post I would like to do a short intro to HDR photography, when to use and when not to use it and the challenges when you need to merge lots of HDR photos and the motivation for automation.
If you would like to know how the automated process that I propose straight away, you can jump to the last section "The Automated Process for Merging HDR Photos in Adobe Lightroom".


## What is HDR?

HDR stands for High Dynamic Range. In photography, it refers to a technique that combines multiple images taken at different exposures to produce a single photograph with a wider range of brighness (dynamic range). This method ensures that both the darkest and brightest areas of a scene are well-exposed, capturing details that might be lost in a single shot.

HDR photography relies on a method called _exposure bracketing_. This involves taking several photos of the same scene at varying exposure levels — typically underexposed, correctly exposed, and overexposed. These images are then merged to create a composite that captures the full dynamic range of the scene.

![Exposure bracketing](/images/posts/exposure_bracketing.jpg)

TODO Add arrows and the final merged image for the image above.

Merging of the photos can be done automatically by the camera, or the camera can save the separate shots and you can later use software to merge them to the single image.

Modern smartphones, like Apple's iPhones, utilize HDR to automatically enhance photos: they automatically detect high-contrast scenes, take several shots in this case and merge them into a single image. All of this happens automatically and behind the scenes.

Specialized cameras, such as mirrorless and point and shoot cameras, frequently also support HDR.

- You can select a special mode (such as [Auto HDR in Sony cameras](https://www.sony.com/electronics/support/articles/00012101)), and the camera will take images with different exposures, merge them, and save as JPEG image (RAW format is usually not supported in this case).
- They also support a more flexible appoach: use [exposure bracketing](https://www.mikesmithphotography.com/videos/exposure-bracketing) to take images with different exposures (which can be saved in RAW format), and later merge them with specialized software. This is the most flexible approach, but it requires extra work.

TODO Briefly describe how to enable this in Sony cameras.


## When to Use HDR Photos?

HDR is particularly effective in situations where there’s a significant difference between the brightest and darkest areas of a scene. Some examples are:

- **Landscape photography**: Capturing details in both bright skies and shadowed foregrounds.
- **Interior photography**: Showcasing room details while preserving window views. Usually 
- **Backlit subjects**: When the main subject is against a strong light source, HDR can balance the exposure to reveal details in both the subject and background.

The photo below is an example of HDR photo that I took in Warner Brothers Studio Harry Potter Tour. It shows a dimly lit street with shady shops, but the Weasleys’ Wizard Wheezes shop is bright and colourful. I used exposure bracketing to take 3 photos with different exposures, and then combined them with Lightroom to get more details in dark areas, but at the same time making sure that the bright shop is not overexposed.

![Diagon Alley from Harry Potter as HDR photo example](/images/posts/hdr-photo-1.jpg)

The interior of a little church in the photo below was shot using iPhone. The smartphone has automatically recognized that this is a high-contrast scene and automatically produced HDR photo. As a result, we can see the view through the windows (even though it is still overexposed, since the day was unusually sunny).

![Henton Chapel from Chiltern Open Air Museum, photo with iPhone in HDR](/images/posts/hdr-photo-iphone.jpg)

When not to use HDR?

- **Scenes with movement**: HDR requires multiple exposures; moving subjects can lead to ghosting or blurring. Lightroom provides Deghosting parameter when merging HDR photos which can help with small movements, but the photos can't be merged effectively when the movement is too big (TODO find better adjective).
- **Low-contrast scenes**: Applying HDR to scenes without significant contrast may result in flat or unnatural images.
- **Portraits**: HDR can exaggerate skin imperfections, making it less suitable for flattering portraits.

Potential problems with overusing HDR:

- **Unnatural Appearance**: Excessive HDR processing can lead to images that look overly processed and unrealistic.
- **Increased Noise**: Combining multiple exposures can amplify noise, especially in darker areas.
- **Halos and Artifacts**: Improper alignment or excessive tone mapping can introduce halos around objects and other visual artifacts.

The photo with Goblin Teller below was shot with a point-and-shoot camera (which has smaller dynamic range than mirrorless cameras) and later processed as HDR image. This allowed the recover the details of the brightly lit face of Goblin, but at the same time the photo lacks depth, the background is not as clearly separated, so the image looks quite flat.

![Goblin Teller as HDR photo example](/images/posts/hdr-photo-3.jpg)

The photo below of Harry Potter and The Monster Book of Monsters was shot with the same camera and also merged as HDR image. You can notice quite a lot of noise in darker areas which was amplified after HDR merge.

![Harry Potter and The Monster Book of Monsters as HDR photo example](/images/posts/hdr-photo-5.jpg)

TODO: Make the photos smaller in size, resize them.

In many cases it is possible to tell in advance which photo will look better in HDR or as a regular photo, but in some cases it is not quite obvious. The best approach could be to take photos with exposure bracketing when in doubt and later review photos on computer and decide which version to keep.


## Merging HDR Photos with Adobe Lightroom

Several specialized software can be used for merging these photos on your computer, such as [Photomatrix](https://www.hdrsoft.com/), [LR/Enfuse](https://www.photographers-toolbox.com/products/lrenfuse.php) and many others. Adobe Lightroom also provides a capability to merge HDR photos.

Personally I use Lightroom (non-Classic version). The subscription comes with 1TB online storage for photos. This makes the photos accessible from all Lightroom apps (with the desktop app, the the iPad app or even in the web), and all the changes and adjustments are synchronized and stored globally in the cloud. This allows me to process photos on my computer when I am at home, or on my iPad when I am on the go.

The process for merging HDR photos in Adobe Lightroom is mostly manual:

1. **Detect groups of photos**. At first, we need to identify the group of photos which were shot with exposure bracketing. I don't use this mode for all photos, but only in situations when I think that the scene is high contrast and the photo could benefit from HDR merging. As a result, the photos are usually a mix of single exposure and exposure bracketed photos. I am trying to visually identify such groups of photos and use "Info" window to double check the capture time (which should be very close in this group).
2. **HDR Merge each group**. Once the group is visually identified, I select all photos in the group and call context menu "Photo Merge -> HDR Merge..." (or use shortcut `Control + H`). This shows "HDR Merge" dialog which provides an overview of the final image and several configuration parameters (such as "Deghost Amount" which TBD describe). Pressing "Merge" button creates a job to merge HDR photo.

![HDR Merge in Lightroom](/images/posts/lightroom_hdr_merge.jpg)

As can be seen, the process is very manual:
- Detecting exposure bracketed photos is not automated in Lightroom, so I need to manually find and select them, which takes time, because I need to double check that the photos were really shot as a group. Unfortunately, Lightroom does not show exposure compensation values, so I have to rely on capture date for this.
- Merging HDR photos takes quite a lot of time and I need to initiate this for every group of photos.

As you can see, this process does not scale very well, especially in the following situations:
- Merging a large number of images, especially when you get back from a long trip.
- Working with mixed photo collections where not all files are exposure bracketed (which is usually the case, since I don't use exposure bracketing when not needed).
- Managing different burst numbers in your shooting sequence. TBD describe that it could be 3, 5, etc image.

Adobe Lightroom _Classic_ version provides several features that can automate the process.

First of all, it provides an "Auto-Stack by Capture Time" feature (this feature is not yet available in the non-Classic version). This involves selecting the photos and then using menu Photo -> Stacking -> Auto-Stack by Capture Time.

![Auto-Stack by Capture Time in Lightroom](/images/posts/lightroom_auto_stack.png)

In the dialog that is shown you need to input the time threshold between the photos to auto stack. This method is useful, because exposure bracketed photos are shot in quick succession. However, I found that this method of setting the precise threshold is not very reliable for the photos that I had: no matter how much I tweak this parameter, I never get the all the exposure bracketed photos to be grouped correctly. One approach which is usually recommended is to make sure you have a small delay when shooting different photos, so that auto stacking later in software could be more reliable. However, this advice does not help if you already have the photos to process. It also complicates shooting photos, since this is one extra thing to think about.

Once the photos are auto-stacked, you can select all stacks and invoke "HDR Merge" command (from the menu or using the same `Control + H` key combination). This will start a job to merge each stack and produce HDR photos in batch mode. At this moment you can sit back, relax and return to computer when the merging is finished. However, note that the same trick would not work in non-Classic Lightroom version: selecting stacks and calling "HDR Merge" would only merge the last selected stack.

These tricks to automate HDR merge in Lightroom Classic version are described in this [YouTube video "Automate HDR Image Merging in Adobe Lightroom \| Automate Your Exposure Bracketing Photo Workflow"](https://www.youtube.com/watch?v=wFbQ-djJ_sY) in detail.


## Creating a New Lightroom Plugin to Automate Merging HDR Photos

To overcome these problems mentioned above and make the process of HDR merging more automated and more reliable, I have created a small plugin: [Lightroom Auto Stacker Plugin](https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker). As indicated in the name, the plugin is specifically aimed at automating the 1st step: detecting groups of exposure bracketing photos and auto-stacking them.

Instead of using time stamps, such as "Auto-Stack by Capture Time" dialog in Lightroom, the tool is relying on EXIF metadata that the camera stores with each image.

TODO Put a little background about what EXIF data is. Also mention [ExifTool](https://exiftool.org/) and provide some overview of this tool. Say that it is a really robust tool, supports many file formats.

Wearing my data scientist hat, let's do some data analysis. Below are some EXIF fields for some files that I took with a Sony camera.

| SourceFile                     | DSC02107.ARW         | DSC02108.ARW         | DSC02109.ARW         | DSC02110.ARW         |
|--------------------------------|----------------------|----------------------|----------------------|----------------------|
| EXIF:DateTimeOriginal          | 2025:03:15 17:35:41  | 2025:03:15 17:36:56  | 2025:03:15 17:36:56  | 2025:03:15 17:36:56  |
| EXIF:ExposureMode              | 0                    | 2                    | 2                    | 2                    |
| EXIF:ExposureCompensation      | 0.3                  | 0.3                  | -0.7                 | 1.3                  |
| MakerNotes:ReleaseMode         | 0                    | 5                    | 5                    | 5                    |
| MakerNotes:SequenceImageNumber | 1                    | 1                    | 2                    | 3                    |
| MakerNotes:SequenceLength      | 1                    | 3                    | 3                    | 3                    |

The photo `DSC02107.ARW` was taken as a single exposure photo. And then I took a photo with exposure bracketing (using the mode of 3 exposures and exposure compensation as 1.0).

TODO Is it safe to say that "EXIF:" fields are common for all camera makers, but "MakerNotes:" are speciic to a camera maker.
Please note that the current plugin supports Sony cameras only. You can see the whole list of EXIF tags for sony here: [Sony Tags](https://exiftool.org/TagNames/Sony.html). I plan to generalize this tool for other camera makers.

Let's take a look at these parameters:

- TODO Explain what the fields EXIF:ExposureMode and MakerNotes:ReleaseMode correspond to. You can notice that for the first photo the values for both are 0 (TODO what does it mean?) But for the next 3 photos the values are 2 and 5 correspondingly (TODO explain what these values correspond to). The plugin that I have implemented uses these fields to detect exposure bracketed photos that should be merged.
- The next useful parameter is MakerNotes:SequenceLength. TODO: What does it mean? For single exposure photos the the sequence length is just 1, but for exposure bracketed images this is the number of images in sequence (in our case 3 photos). The tag MakerNotes:SequenceImageNumber index of the image in sequence.
- EXIF:ExposureCompensation: the exposure bracketed images will show different exposure compensation. In this case my default exp comp in camera was 0.3. I used exp bracket with 3 shoots, comp 1.0. So the first shot has the default 0.3, second: 0.3-1.0=-0.7, the third: 0.3+1.0=1.3.

The design of the plugin was hugely influenced by what Lightroom SDK supports, since the API is quite limited. This has lead to design decisions for this plugin.

The solution is divided into two components:

Python Script:
Detects exposure-bracketed image groups using EXIF metadata. It then produces a descriptive file that outlines the detected groups. This method is more reliable than relying solely on capture timing.

Lightroom Plugin:
Reads the group description file and imports the grouped images into Lightroom, automatically stacking them in preparation for HDR processing. Once the stacks are created, you can use Lightroom's built-in HDR merge functionality to batch process the stacks.


## The Automated Process for Merging HDR Photos in Adobe Lightroom

![Automated HDR Merge Process](/images/posts/automated-hdr-merge.gif)

TODO Can I integrate youtube video into medium and blog posts? What would be the best approach? Can I upload outside youtube not to have that dependency?

The installation instructions for the plugin are the following:

Python Script

1. **Install Python** (if not already installed).
2. **Clone the Repository:**
   ```sh
   git clone https://github.com/anton-dergunov/lightroom-hdr-auto-stack.git
   cd lightroom-hdr-auto-stack
   ```
3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

Lightroom Plugin

1. **Launch Adobe Lightroom Classic**  
   (Note: The non-Classic version does not support plugins as of now.)
2. **Open Plug-in Manager:**
   - Navigate to **File > Plug-in Manager**.
3. **Add the Plugin:**
   - Click **Add** and select the `auto-stacker.lrplugin` folder.
   - Enable the plugin once added.

The instructions for using the plugin are the following:

1. **Detect Bracketed Images and Generate Groups File:**
   Run the Python script to analyze your photos and create a group description file.
   ```sh
   python group_sony_bracketed_photos.py --input /path/to/photos --output /path/to/groups.txt
   ```
   You may specify a different photo file extension with `--extension` (default is `ARW`).

2. **Import and Auto-Stack in Lightroom:**
   - In Lightroom Classic, go to **Library > Plugin Extras > Import and Auto Stack Photos**.
   - Provide the path to the generated groups file.
   - Wait for the images to be imported and automatically stacked.

3. **Batch Create HDR Images:**
   - Navigate to the folder containing the imported stacks.
   - Collapse all stacks via **Photo > Stacking > Collapse All Stacks**.
   - Select all stacks (**Edit > Select All**) and execute **Photo > Photo Merge > HDR...**.
   - Lightroom will initiate a batch job to merge each stack with previously used settings (e.g., Deghost Amount). Please note that this process can be time-consuming when handling a large number of images.
   - This batch processing ensures that all HDR images are created upfront, allowing for a streamlined photo culling process where HDR and original exposures are available for direct comparison.

4. **Access the Final HDR Images:**
   - If you are using Lightroom Classic, you can continue working with the HDR images directly within the library. To quickly find the HDR images, you can filter the Library View by the `.dng` extension.
   - If you primarily use the the non-Classic version of Lightroom, you can export the created HDR images. The generated HDR images are saved in the same folder as the original files, typically named using the first image’s filename followed by `-HDR.dng`, so you can copy them directly as well.


When I come home from a walk shooting photos, I use this plugin to automatically merge all HDR photos. This process is automated, but it takes some time to run. When this is ready, I import both the original photos and the generated HDR photos to Adobe Cloud storage (TBD is this the correct name)? This is the useful pre-processing, that allows me to later process and do photo selection all in one go (and decide if I should keep the HDR or any original photos that they were created from). I can do this either on my computer or on iPad. After this pre-processing step, Using this process allows me to see what HDR images look like. I don't always prefer HDR photo. This all depens on case by case basis, and sometimes hard to say in advance. So this saves me time. If I don't like how some photos were merged (for example, there is some ghosting), I can manually recreate the HDR photos in Lightroom with different settings.


References:
- [Lightroom Auto Stacker Plugin](https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker)
- [What is the Difference between Auto High Dynamic Range (HDR) and D-Range Optimizer (DRO)?](https://www.sony.com/electronics/support/articles/00012101)
- [The Ultimate Guide to Exposure Bracketing](https://www.mikesmithphotography.com/videos/exposure-bracketing)
- [HDR Photography is NOT DEAD!](https://f64academy.com/hdr-photography-is-not-dead/)
- [Photomatrix](https://www.hdrsoft.com/)
- [LR/Enfuse](https://www.photographers-toolbox.com/products/lrenfuse.php)
- [YouTube video "Automate HDR Image Merging in Adobe Lightroom \| Automate Your Exposure Bracketing Photo Workflow"](https://www.youtube.com/watch?v=wFbQ-djJ_sY)
- [ExifTool](https://exiftool.org/)
- TODO include other links


---


**High Dynamic Range (HDR) photography is a collection of photographic techniques that aim to capture and then display a wider range of luminosity levels than can be achieved using standard photographic techniques**. As you know, "HDR" is an abbreviation for "High Dynamic Range". To understand this fully, let's break down what "range," "dynamic," and "high" mean in this context. The **"range"** refers to the spectrum between the lightest and darkest parts of a scene. Your eyes are **"dynamic"** because they can adjust to perceive details across these extremes of light and dark. However, a **conventional single photographic exposure** has a limited ability to capture this entire spectrum when there is a significant difference between the brightest highlights and the deepest shadows. **HDR photography seeks to create images with a "high" dynamic range**, more closely resembling the capabilities of human vision and even extending beyond it to create previously impossible images.

**Limitations of Standard Digital Sensors:**

A key reason for using HDR techniques is the **inherent limitation of digital camera sensors** in capturing the full dynamic range that our eyes can perceive. Unlike our eyes, a camera sensor in a single exposure struggles to record detail in both very bright and very dark areas simultaneously. When the dynamic range of a scene exceeds the sensor's capacity, some areas will inevitably be **"clipped"** – either highlights will be overexposed, losing all detail and appearing pure white, or shadows will be underexposed, becoming pure black with no discernible information. Current digital camera sensors cannot even reach a dynamic range of 1000:1, whereas panchromatic film could capture up to 10,000:1. This limitation means that in many real-world scenarios, a single photograph will fail to capture the scene as we experience it.

**A Look at the History:**

While HDR has gained significant traction with the advent of digital photography, the **awareness of the limitations of exposure range is not new**. Even in the early days of photography, practitioners sought ways to overcome these limitations. For instance, [Gustave Le Gray](https://en.wikipedia.org/wiki/Gustave_Le_Gray)'s 19th-century seascapes, which combined separately exposed negatives for the sky and the sea, can be considered early examples of HDR thinking, and his prints have recently fetched record prices at auction. As photography progressed, [Ansel Adams](https://en.wikipedia.org/wiki/Ansel_Adams) is renowned for his prints' wide tonal range, achieved through meticulous exposure and development using his **zone system**, as well as extensive **dodging and burning** in the darkroom (TBD Please add some links about this). He even used a custom-modified enlarger to extend the dynamic range of his images. Therefore, the concept of extending dynamic range has been a long-standing pursuit in photography. Digital photography now allows for simpler methods to achieve HDR results that were previously impossible.


[![Brig upon the Water](/images/posts/brig_upon_the_water.jpg)](https://upload.wikimedia.org/wikipedia/commons/c/cd/Gustave_Le_Gray_-_Brig_upon_the_Water_-_Google_Art_Project.jpg)
*Brig upon the Water* by Gustave Le Gray, 1856. Public domain. Source: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Gustave_Le_Gray_-_Brig_upon_the_Water_-_Google_Art_Project.jpg#).

[![The Tetons and the Snake River](/images/posts/the_tetons_and_the_snake_river.jpg)](https://upload.wikimedia.org/wikipedia/commons/2/21/Adams_The_Tetons_and_the_Snake_River.jpg)
*The Tetons and the Snake River* by Ansel Adams, 1942. Public domain. Source: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Adams_The_Tetons_and_the_Snake_River.jpg#).


**The Modern HDR Process:**

The creation of an HDR image typically involves two main phases: **shooting multiple exposures** and **processing these exposures** using specialised software.

*   **Shooting for HDR:**
    *   This often involves **capturing a sequence of images of the same scene with varying exposure levels**, a technique known as **bracketing**. These different exposures ensure that detail is captured in the brightest, midtone, and darkest areas of the scene. Your camera may have an **auto-bracketing function** that automatically takes a series of shots at different exposures. You can also bracket **manually** by adjusting the shutter speed (or sometimes aperture or ISO) between each shot. Using **continuous shooting mode** can help capture these bracketed exposures quickly.
    *   To ensure proper alignment of the multiple exposures, especially for later merging, using a **tripod** is highly recommended. This prevents unwanted shifts between frames. However, even with a tripod, movement within the scene (**camera motion** or subject movement) can occur and needs to be addressed during processing.
    *   To capture the **entire dynamic range** of a scene, you need to ensure that your bracketed exposures range from one where the highlights are correctly exposed (not blown out) to one where the shadows contain detail (not pure black). The number of exposures required depends on the dynamic range of the scene; sometimes two exposures are sufficient, while other high-contrast situations may require more. One technique is to continue shooting until the histogram of the darkest exposure shows detail in what appear to be shadow areas, even if the lighter parts of the image look completely washed out.

*   **HDR Processing (Tone Mapping):**
    *   Once you have your bracketed exposures or multiple versions of a RAW file, they need to be combined using **HDR software**. Popular software options mentioned in the sources include **Adobe Camera RAW, Photoshop, Nik HDR Efex Pro, Photomatix**, as well as **FDRTools, PFSTools, and EasyHDR**. These programs merge the multiple exposures into a single HDR image, which contains a much greater range of luminance values than a standard image format.
    *   Since standard display devices like computer monitors and printed photos have a limited dynamic range (**Low Dynamic Range - LDR**), the high dynamic range of the merged image needs to be compressed into a viewable format through a process called **tone mapping**. **Tonemapping operators (TMOs)** are the algorithms within HDR software that perform this compression. A simple linear compression of the HDR image would result in an image that is too dark with a lack of detail in the shadows. Therefore, tone mapping must consider how we perceive light.
    *   **Common artefacts** can arise during tone mapping. **Halos** are bright or dark fringes that can appear around high-contrast edges, often caused by excessive local contrast adjustments. **Ghosting** occurs when there was movement in the scene between the bracketed exposures, resulting in semi-transparent overlaps of moving objects. **Noise** and exaggerated textures can also become more apparent, especially when trying to maximise fine detail. An **artificial appearance**, with incorrect tones, colours, and exaggerated microcontrast, can result from excessive or incorrect tonemapping. Many HDR software programs offer tools to mitigate these issues, such as ghost reduction and smoothing options.
    *   Often, the initial tone-mapped image will benefit from **further post-processing** in image editing software like Lightroom or Photoshop. This can involve adjusting levels and curves, refining contrast, sharpening, colour correction, and selectively editing specific areas to achieve the desired final look.

---


**HDR: Beyond the "Gritty" Look:**

It is a common misconception that all HDR images have an unnatural, overly processed, or "gritty" appearance. However, **HDR is a versatile tool that can be used to create very subtle and natural-looking images**. The final aesthetic is largely determined by the photographer's artistic vision and the specific tone mapping settings applied. Carefully applied HDR can enhance the tonal range and detail in a photograph without being overtly noticeable. In fact, some of the most impactful HDR images are those where the viewer may not even realise HDR techniques were used. The key is to exercise good artistic judgment and avoid pushing the settings to extremes that result in an artificial look. **Less is often more** in achieving a visually pleasing and impactful HDR image.

**Types of High-Range Scenes:**

Scenes with high dynamic ranges arise for specific reasons, leading to different types of situations that may require HDR techniques:

*   **Progressive brightening** can occur in scenes like a detail of an old vaulted ceiling lit from beneath, where there is a gradual increase in brightness.
*   **Small bright against dark** is typical of spotlighting effects, whether artificial or natural, such as sunlight illuminating a small area within a darker scene.
*   A **window to a sunlit exterior** is a classic example of a high dynamic range scene with strong segmentation between the bright outside and the darker interior.
*   A **divided frame**, such as a landscape with a horizon against a bright sky, presents a significant contrast difference across a defined boundary.

Understanding these different types of high-range scenes can influence how you approach both the shooting and the tone mapping process.

**Applications of HDR:**

HDR techniques are employed across various photographic genres to enhance the final image:

*   **Landscapes:** To capture the often vast difference in brightness between the sky and the foreground, revealing detail in both.
*   **Cityscapes and Architecture:** To balance the extreme lighting differences in urban environments and bring out textures and details in buildings, both in bright sunlight and shadow.
*   **Interiors:** Particularly useful for capturing detail when shooting into bright windows from a darker interior.
*   **Flowers:** To control the lighting and capture the subtle, translucent details of petals.
*   While more care is needed, HDR can even be applied to **portraits** for specific artistic effects, though attention must be paid to subject movement and potential unnatural skin tones.


---

TODO Include photos and videos this way:

[![Diagon Alley - HDR](path/to/diagon-alley-thumb.jpg)](path/to/diagon-alley-full.jpg)  
*Diagon Alley (HDR example)* – Warner Bros Tour London. Photo by the author.

[![Henton Chapel - HDR](path/to/henton-chapel-thumb.jpg)](path/to/henton-chapel-full.jpg)  
*Henton Chapel (iPhone HDR)* – Chiltern Open Air Museum. Photo by the author.

[![Goblin Teller - HDR](path/to/goblin-teller-thumb.jpg)](path/to/goblin-teller-full.jpg)  
*Goblin Teller (HDR example)* – Warner Bros Tour London. Photo by the author.

[![The Monster Book of Monsters - HDR](path/to/monster-book-thumb.jpg)](path/to/monster-book-full.jpg)  
*The Monster Book of Monsters (HDR example)* – Warner Bros Tour London. Photo by the author.

<iframe width="560" height="315" src="https://www.youtube.com/embed/YOUR_VIDEO_ID" frameborder="0" allowfullscreen></iframe>



