# Markdown Image Server Migration Tool

If in your markdown documents, the images references are all external links and may go down at any moments, you may want to migrate all the images to a server under your control.
This tool provides functional API that scan the document for image urls, download all desired images to a specified directory, and relabel the image URLs in the markdown document to point to the server hosting the downloaded images.

## Assumptions

The ideal operation condition of the tool includes:

1. All markdown files are encoded in utf-8
2. The new image server's image url must be in the form of `$host_img_root_dir$/$img_name$`. The image name must be written exactly at the end of the new url. Do not use Google Drive, GooglePhoto or OneDrive as they hash the file endpoints. This condition is a _must_.
3. All image files are saved as PNG (JPG and GIF files may work).
4. A reliable internet connection for image download.

## Workflow Overview

1. Provide the project directory, in which all markdown files will be scanned.
2. `ImageServerMigration.download_photos_from_all()` to download all images to a specified directory.
3. User manually upload the directory to a image hosting server.
4. User specify the host server url with image root directory. By calling `ImageServerMigration.relabelling_effort(host_img_root_dir)`, all applicable image links will be relabelled.

## Developer's Note: Auto-Download Procedure

1. Use a dictionary `imginfo`, in which the key is the current image URL and value is the name of the image.
2. Create a user-specified directory to dump all downloaded images
3. Open all markdown files found from a specified directory
4. For each image link encountered, create a key-value pair in `imginfo` (the image name is specified in the markdown format), then download the image. Note that two images may have duplicate names, the duplicate image will have a number appended to it.
5. After all markdown files are processed, save `imginfo` to disk by dumping it to a json file.

## Developer's Note: Markdown URL Re-labelling

1. Parse `imginfo` json to a map (if the program just start up)
2. Open all markdown files
3. For each image link encountered, use URL as key to find the name of the image downloaded
4. Prepend the new image host server url to the image name, re-label the url in place
5. Update the key value in `imginfo` (remove old key-value pair and add new)
