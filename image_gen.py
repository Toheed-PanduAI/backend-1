import requests
from models import StabilityGenerateImageRequest, StabilityImageToVideoRequest
from fastapi import HTTPException,  File, UploadFile, Form


def stability_generate_image(api_key, data: StabilityGenerateImageRequest):
    url = f"https://api.stability.ai/v2beta/stable-image/generate/{data.model}"
    headers = {
        # "authorization": f"Bearer sk-MYAPIKEY",
        "authorization": api_key,
        "accept": "image/*"
    }
    request_data = {
        "prompt": data.prompt,
        "output_format": data.output_format
    }

    if data.negative_prompt:
        request_data["negative_prompt"] = data.negative_prompt
    if data.aspect_ratio:
        request_data["aspect_ratio"] = data.aspect_ratio
    if data.seed:
        request_data["seed"] = data.seed

    response = requests.post(url, headers=headers, files={"none": ''}, data=request_data)

    if response.status_code == 200:
        return response.content
    else:
        raise HTTPException(status_code=response.status_code, detail=str(response.json()))
    
def stability_image_to_video_start(api_key, image_file: UploadFile, data: StabilityImageToVideoRequest):
    url = f"https://api.stability.ai/v2beta/image-to-video"
    headers = {
        # "authorization": f"Bearer sk-MYAPIKEY",
        "authorization": api_key,

    }
    files = {
        "image": (image_file.filename, image_file.file, image_file.content_type)
    }
    data_dict = {
        "seed": data.seed,
        "cfg_scale": data.cfg_scale,
        "motion_bucket_id": data.motion_bucket_id
    }

    response = requests.post(url, headers=headers, files=files, data=data_dict)

    if response.status_code == 200:
        return response.json().get('id')
    else:
        raise HTTPException(status_code=response.status_code, detail=str(response.json()))

def stability_fetch_video_result(api_key, generation_id: str):
    url = f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}"
    headers = {
        'accept': "video/*",  # Use 'application/json' to receive base64 encoded JSON
        # 'authorization': f"Bearer sk-MYAPIKEY",
        "authorization": api_key,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 202:
        return "Generation in-progress, try again in 10 seconds."
    elif response.status_code == 200:
        with open("video.mp4", 'wb') as file:
            file.write(response.content)
        return "Generation complete! Video saved as 'video.mp4'."
    else:
        raise HTTPException(status_code=response.status_code, detail=str(response.json()))


