---
title:     "Automating HDR Photo Creation in Adobe Lightroom"
date:      2025-04-02
permalink: /posts/2025/04/automating-hdr-photo-creation-in-adobe-lightroom
tags:
  - automation
  - photography
---

High Dynamic Range (HDR) photography enables photographers to capture a broader range of light and detail than standard imaging techniques allow. It involves taking multiple shots of the same scene at varying exposure levels — typically underexposed, correctly exposed, and overexposed — and then merging them to create a single image with higher dynamic range.

![Exposure bracketing](/images/posts/exposure_bracketing.jpg)

Merging of the photos can be done automatically by the camera, or the camera can save the separate shots and you can later use software to merge them to the single image.

Apple's iPhones utilize HDR to automatically enhance photos: they automatically detect high-contrast scenes, take several shots in this case and merge them into a single image, all behind the scenes. Specialized cameras, such as mirrorless and point and shoot cameras, frequently also support HDR.

- You can select a special mode (such as [Auto HDR in Sony cameras](https://www.sony.com/electronics/support/articles/00012101)), and the camera will take images with different exposures, merge them, and save as JPEG image (RAW format is usually not supported in this case).
- They also support a more flexible appoach: use [exposure bracketing](https://www.mikesmithphotography.com/videos/exposure-bracketing) to take images with different exposures (which can be saved in RAW format), and later merge them with specialized software. This is the most flexible approach, but it requires extra work.

Several specialized software can be used for merging these photos on your computer, such as [Photomatrix](https://www.hdrsoft.com/), [LR/Enfuse](https://www.photographers-toolbox.com/products/lrenfuse.php) and many others. Adobe Lightroom also provides a capability to merge HDR photos.

![HDR Merge in Lightroom](/images/posts/lightroom_hdr_merge.jpg)

However, the process for HDR photo creation in Lightroom is mostly manual and does not scale very well when you have lots of images to merge, because you need to individually select image groups and invoke the HDR merge command for each stack.

While Lightroom Classic provides an "Auto-Stack by Capture Time" feature, it depends heavily on a precise time threshold between shots. This method can be fragile for photo collections captured under varying conditions, and the non-Classic version of Lightroom does not support auto-stacking at all.

![Auto-Stack by Capture Time in Lightroom](/images/posts/lightroom_auto_stack.jpg)



What is HDR?

![TBD](/images/posts/hdr-photo-1.jpg_)


When to use HDR photos?
- Very bright areas (window)

Problems with HDR photos:
- Photos with moving subjects
- Ghosts
- Sometimes makes the images too flat
- "HDR look"


iPhones automatically do HDR photos. They detect good opportunities and create images automatically.
Some cameras (DJI Action 5) also do HDR videos.

Specialized cameras also have this function. They provide a possiblity to create exposure bracketed images, and then
- Either automatically merge the image and create JPEG file
- If you shoot in RAW, they store these images separately, and you need to use software to merge them after shooting

BTW, can they do both?

TODO Show how to enable this in Sony cameras

Various software exist for HDR merge (including supporting batch merging).
Personally I use Lightroom (non-Classic version). This allows me to store the photos in the cloud and process them on my iPad when I have free time for this.

Lightroom supports HDR merge, but the process to merge is mostly manual. TODO describe from the readme file.

To overcome these problems, I have created a small plugin to automate this work.
[Lightroom Auto Stacker Plugin](https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker)

Lightroom Classic and many other tools timestamp to auto-stack images. I found this to be not too reliable. Usually the advice is to space out your series when shooting bursts with exposure bracketing.

Instead of using time stamps, the tool is relying on EXIF metadata that the camera stores with each image.
Wearing my data scientist hat. Below is some data analysis for this the EXIF fields.

Introduce EXIF and exiftool. Really robust tool, supports many file formats.

[ExifTool](https://exiftool.org/)

Show demo of this tool in command line.

I am using Sony cameras. Some EXIF metadata are custom for each camera make (MakerNotes? is this per-maker?) The script currently only supports Sony.

| SourceFile                     | DSC02107.ARW         | DSC02108.ARW         | DSC02109.ARW         | DSC02110.ARW         |
|--------------------------------|----------------------|----------------------|----------------------|----------------------|
| EXIF:DateTimeOriginal          | 2025:03:15 17:35:41  | 2025:03:15 17:36:56  | 2025:03:15 17:36:56  | 2025:03:15 17:36:56  |
| EXIF:ExposureMode              | 0                    | 2                    | 2                    | 2                    |
| EXIF:ExposureCompensation      | 0.3                  | 0.3                  | -0.7                 | 1.3                  |
| MakerNotes:ReleaseMode         | 0                    | 5                    | 5                    | 5                    |
| MakerNotes:SequenceImageNumber | 1                    | 1                    | 2                    | 3                    |
| MakerNotes:SequenceLength      | 1                    | 3                    | 3                    | 3                    |

TODO Describe the approach:

- The usual shooting modes: EXIF:ExposureMode is 0 and MakerNotes:ReleaseMode is 0 (or any other values)
- When EXIF:ExposureMode is 2 and MakerNotes:ReleaseMode is 5: what does it mean? Like for the images `DSC02108.ARW`, `DSC02109.ARW`, `DSC02110.ARW`.
- MakerNotes:SequenceLength is the number of images in sequence (exposure bracket 3, 5, etc)
- MakerNotes:SequenceImageNumber: sequential number of the image
- EXIF:ExposureCompensation: the exposure bracketed images will show different exposure compensation. In this case my default exp comp in camera was 0.3. I used exp bracket with 3 shoots, comp 1.0. So the first shot has the default 0.3, second: 0.3-1.0=-0.7, the third: 0.3+1.0=1.3.

The idea of the tool 

TODO Describe how auto stacking was designed.

The process that I use to use this plugin...

Import back into Adobe Lightroom (non-Classic)
Use iPad for photo selection. After this pre-processing step, Using this process allows me to see what HDR images look like. I don't always prefer HDR photo. This all depens on case by case basis, and sometimes hard to say in advance. So this saves me time. If I would like, I can manually recreate the HDR photos in Lightroom with different settings.


References:
https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker
- [What is the Difference between Auto High Dynamic Range (HDR) and D-Range Optimizer (DRO)?](https://www.sony.com/electronics/support/articles/00012101)
- [The Ultimate Guide to Exposure Bracketing](https://www.mikesmithphotography.com/videos/exposure-bracketing)

Books on HDR
Links to other software

