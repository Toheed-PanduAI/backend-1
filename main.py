import uvicorn
import httpx
from fastapi import FastAPI, Response, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from io import BytesIO  
from starlette.middleware.cors import CORSMiddleware
import json
import stripe
import os
import requests
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from supertokens_python import init, get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.multitenancy.asyncio import list_all_tenants
from supertokens_python.recipe.userroles import UserRoleClaim
from elevenlabs import Voice, VoiceSettings, play
import supertoken_config
import db
import utils
import speech_synthesis
from models import Item, VoiceResponse, SubscriptionItem, PriceResponse, CancelItem, UpdateItem, User, Permission, Payment, Plan, Subscription, VideoTask, TranscriptionResponse, ImageGenerationResponse, Message, ChatCompletionResponse
from dotenv import load_dotenv
from googleapiclient.discovery import build
# from gmail_oauth import get_credentials

load_dotenv() 

# Setup Stripe python client library
# stripe.api_key =  os.getenv('STRIPE_SECRET_KEY')
# stripe_publishable_key = os.getenv('STRIPE_PUBLIC_KEY'),
stripe.api_key =  "sk_test_51PQnqhP3fxV3o3WtOlLEclN5cK0FolvRFevDW0l9gkydYC89cR8KXV7CxS5051wbxk4eHjY11DU61G3XN1E9zu9s00YqAmKQXN"
stripe_publishable_key = "pk_test_51PQnqhP3fxV3o3WtbvtjGmdVksLrTdMTKEpwS29TVLjz3En9cQK4XUbyO1X3UNlbVdBJgolhXidxaaQZiETR9bgE00fY8LeOYm",

# MathPix API credentials
# mathpix_api_id = os.getenv("MATHPIX_APP_ID")
# mathpix_api_key = os.getenv("MATHPIX_APP_KEY")

# ElevenLabs URL
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/voices"

init(
    supertokens_config=supertoken_config.supertokens_config,
    app_info=supertoken_config.app_info,
    framework=supertoken_config.framework,
    recipe_list=supertoken_config.recipe_list,
    mode="asgi",
)

app = FastAPI(title="PanduAI Backend", version="0.1.0")

app.add_middleware(get_middleware())

@app.get("/sessioninfo")    
async def secure_api(session: SessionContainer = Depends(verify_session())):
    return {
        "sessionHandle": session.get_handle(),
        "userId": session.get_user_id(),
        "accessTokenPayload": session.get_access_token_payload(),
    }

# Permissions and Roles API
@app.get('/create_role')  
async def create_role(role_data: str, permissions: List[str], session: SessionContainer = Depends(
        verify_session()
)):
    try:
        # Add the role to the session
        await supertoken_config.create_role(role_data, permissions)
        return {"status": "OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get('/add_permissions')  
async def create_role(role_data: str, permissions: List[str], session: SessionContainer = Depends(
        verify_session()
)):
    try:
        # Add the role to the session
        await supertoken_config.add_permission_for_role(role_data, permissions)
        return {"status": "OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get('/remove_permissions')  
async def create_role(role_data: str, permissions: List[str], session: SessionContainer = Depends(
        verify_session()
)):
    try:
        # Add the role to the session
        await supertoken_config.remove_permission_from_role(role_data, permissions)
        return {"status": "OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get('/delete_role')      
async def create_role(role_data: str, permissions: List[str], session: SessionContainer = Depends(
        verify_session()
)):
    try:
        # Add the role to the session
        await supertoken_config.delete_role_function(role_data, permissions)
        return {"status": "OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get('/delete_all')  
async def delete_all(session: SessionContainer = Depends(
        verify_session(
            # We add the UserRoleClaim's includes validator
            override_global_claim_validators=lambda global_validators, session, user_context: global_validators + \
            [UserRoleClaim.validators.includes("admin")]
        )
)):
    return {
        "status": "OK",
    }

@app.get('/update_user')  
async def update_user(session: SessionContainer = Depends(
        verify_session(
            # We add the UserRoleClaim's includes validator
            override_global_claim_validators=lambda global_validators, session, user_context: global_validators + \
            [UserRoleClaim.validators.includes("user")]
        )
)):
    return {
        "status": "OK",
    }


# Users API
@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: str):

    user =  db.users_collection.find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@app.post("/users/", response_model=User)
async def create_user(user : dict = Depends(User)):

    if db.users_collection is None:
        raise HTTPException(status_code=500, detail="Database connection not initialized")
    
    # # Check if email is already registered
    # user_exists = await db.users_collection.find_one({"email": user.email})
    # if user_exists:
    #     raise HTTPException(status_code=400, detail="Email already registered")

    user_data = user.dict()
    user_data["password_hash"] = utils.hash_password(user.password_hash)
    user_data["created_at"] = datetime.now()

    result = db.users_collection.insert_one(user_data)
    new_user = db.users_collection.find_one({"_id": result.inserted_id})
    if new_user:
        return User(**new_user)
    
    raise HTTPException(status_code=500, detail="User creation failed")


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user : dict = Depends(User), session: SessionContainer = Depends(verify_session())):
    user_data = user.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["password_hash"] = utils.hash_password(user_data["password"])
        del user_data["password"]

    result = await db.users_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": user_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await db.users_collection.find_one({"_id": ObjectId(user_id)})
    return User(**updated_user)

@app.delete("/users/{user_id}", response_model=User)
async def delete_user(user_id: str, session: SessionContainer = Depends(verify_session())):
    user = await db.users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users_collection.delete_one({"_id": ObjectId(user_id)})
    return User(**user)

# User Permissons API
@app.post("/users/{user_id}/permissions/", response_model=User)
async def update_permissions(
    user_id: str,
    permissions: List[Permission]
):
    user_data = db.users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    db.users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"permissions": [perm.dict() for perm in permissions]}}
    )

    updated_user = db.users_collection.find_one({"_id": ObjectId(user_id)})
    return User(**updated_user)

# Payments API
@app.get("/payments/{payment_id}", response_model=Payment)
async def read_payment(payment_id: str, session: SessionContainer = Depends(verify_session())):
    payment = await db.payments_collection.find_one({"_id": ObjectId(payment_id)})
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return Payment(**payment)

@app.post("/payments/", response_model=Payment)
async def create_payment(payment: Payment, session: SessionContainer = Depends(verify_session())):
    payment_data = payment.dict(by_alias=True)
    payment_data["payment_date"] = datetime.now()
    result = await db.payments_collection.insert_one(payment_data)
    new_payment = await db.payments_collection.find_one({"_id": result.inserted_id})
    return Payment(**new_payment)

@app.put("/payments/{payment_id}", response_model=Payment)
async def update_payment(payment_id: str, payment: Payment, session: SessionContainer = Depends(verify_session())):
    payment_data = payment.dict(by_alias=True, exclude_unset=True)
    result = await db.payments_collection.update_one({"_id": ObjectId(payment_id)}, {"$set": payment_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    updated_payment = await db.payments_collection.find_one({"_id": ObjectId(payment_id)})
    return Payment(**updated_payment)

@app.delete("/payments/{payment_id}", response_model=Payment)
async def delete_payment(payment_id: str, session: SessionContainer = Depends(verify_session())):
    payment = await db.payments_collection.find_one({"_id": ObjectId(payment_id)})
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    await db.payments_collection.delete_one({"_id": ObjectId(payment_id)})
    return Payment(**payment)

# Plans API
@app.post("/plans/", response_model=Plan)
async def create_plan(plan: Plan, session: SessionContainer = Depends(verify_session())):
    plan_data = plan.dict(by_alias=True)
    result = await db.plans_collection.insert_one(plan_data)
    new_plan = await db.plans_collection.find_one({"_id": result.inserted_id})
    return Plan(**new_plan)

@app.get("/plans/", response_model=List[Plan])
async def read_plans(skip: int = 0, limit: int = 10, session: SessionContainer = Depends(verify_session())):
    plans_cursor = db.plans_collection.find().skip(skip).limit(limit)
    plans = await plans_cursor.to_list(length=limit)
    return plans

@app.get("/plans/{plan_id}", response_model=Plan)
async def read_plan(plan_id: str, session: SessionContainer = Depends(verify_session())):
    plan = await db.plans_collection.find_one({"_id": ObjectId(plan_id)})
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return Plan(**plan)

@app.put("/plans/{plan_id}", response_model=Plan)
async def update_plan(plan_id: str, plan: Plan, session: SessionContainer = Depends(verify_session())):
    plan_data = plan.dict(by_alias=True, exclude_unset=True)
    result = await db.plans_collection.update_one({"_id": ObjectId(plan_id)}, {"$set": plan_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    updated_plan = await db.plans_collection.find_one({"_id": ObjectId(plan_id)})
    return Plan(**updated_plan)

@app.delete("/plans/{plan_id}", response_model=Plan)
async def delete_plan(plan_id: str, session: SessionContainer = Depends(verify_session())):
    plan = await db.plans_collection.find_one({"_id": ObjectId(plan_id)})
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.plans_collection.delete_one({"_id": ObjectId(plan_id)})
    return Plan(**plan)

# Subscriptions API
@app.post("/subscriptions/", response_model=Subscription)
async def create_subscription(subscription: Subscription, session: SessionContainer = Depends(verify_session())):
    subscription_data = subscription.dict(by_alias=True)
    result = await db.subscriptions_collection.insert_one(subscription_data)
    new_subscription = await db.subscriptions_collection.find_one({"_id": result.inserted_id})
    return Subscription(**new_subscription)

@app.get("/subscriptions/", response_model=List[Subscription])
async def read_subscriptions(skip: int = 0, limit: int = 10, session: SessionContainer = Depends(verify_session())):
    subscriptions_cursor = db.subscriptions_collection.find().skip(skip).limit(limit)
    subscriptions = await subscriptions_cursor.to_list(length=limit)
    return subscriptions

@app.get("/subscriptions/{subscription_id}", response_model=Subscription)
async def read_subscription(subscription_id: str, session: SessionContainer = Depends(verify_session())):
    subscription = await db.subscriptions_collection.find_one({"_id": ObjectId(subscription_id)})
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return Subscription(**subscription)

@app.put("/subscriptions/{subscription_id}", response_model=Subscription)
async def update_subscription(subscription_id: str, subscription: Subscription, session: SessionContainer = Depends(verify_session())):
    subscription_data = subscription.dict(by_alias=True, exclude_unset=True)
    result = await db.subscriptions_collection.update_one({"_id": ObjectId(subscription_id)}, {"$set": subscription_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    updated_subscription = await db.subscriptions_collection.find_one({"_id": ObjectId(subscription_id)})
    return Subscription(**updated_subscription)

@app.delete("/subscriptions/{subscription_id}", response_model=Subscription)
async def delete_subscription(subscription_id: str, session: SessionContainer = Depends(verify_session())):
    subscription = await db.subscriptions_collection.find_one({"_id": ObjectId(subscription_id)})
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.subscriptions_collection.delete_one({"_id": ObjectId(subscription_id)})
    return Subscription(**subscription)

# Video Tasks API
@app.post("/video_tasks/", response_model=VideoTask)
async def create_video_task(video_task: VideoTask, session: SessionContainer = Depends(verify_session())):
    video_task_data = video_task.dict(by_alias=True)
    video_task_data["created_at"] = datetime.now()
    result = await db.video_tasks_collection.insert_one(video_task_data)
    new_video_task = await db.video_tasks_collection.find_one({"_id": result.inserted_id})
    return VideoTask(**new_video_task)

@app.get("/video_tasks/", response_model=List[VideoTask])
async def read_video_tasks(skip: int = 0, limit: int = 10, session: SessionContainer = Depends(verify_session())):
    video_tasks_cursor = db.video_tasks_collection.find().skip(skip).limit(limit)
    video_tasks = await video_tasks_cursor.to_list(length=limit)
    return video_tasks

@app.get("/video_tasks/{video_task_id}", response_model=VideoTask)
async def read_video_task(video_task_id: str, session: SessionContainer = Depends(verify_session())):
    video_task = await db.video_tasks_collection.find_one({"_id": ObjectId(video_task_id)})
    if video_task is None:
        raise HTTPException(status_code=404, detail="VideoTask not found")
    return VideoTask(**video_task)

@app.put("/video_tasks/{video_task_id}", response_model=VideoTask)
async def update_video_task(video_task_id: str, video_task: VideoTask, session: SessionContainer = Depends(verify_session())):
    video_task_data = video_task.dict(by_alias=True, exclude_unset=True)
    video_task_data["updated_at"] = datetime.now()
    result = await db.video_tasks_collection.update_one({"_id": ObjectId(video_task_id)}, {"$set": video_task_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="VideoTask not found")
    updated_video_task = await db.video_tasks_collection.find_one({"_id": ObjectId(video_task_id)})
    return VideoTask(**updated_video_task)

@app.delete("/video_tasks/{video_task_id}", response_model=VideoTask)
async def delete_video_task(video_task_id: str, session: SessionContainer = Depends(verify_session())):
    video_task = await db.video_tasks_collection.find_one({"_id": ObjectId(video_task_id)})

    if video_task is None:
        raise HTTPException(status_code=404, detail="VideoTask not found")
    
    await db.video_tasks_collection.delete_one({"_id": ObjectId(video_task_id)})
    
    return VideoTask(**video_task)

# Stripe API for payments
@app.get("/price_config")
async def get_config():
    try:
        prices = stripe.Price.list(
            lookup_keys=['sample_free', 'sample_basic', 'sample_premium']
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PriceResponse(
        publishableKey=stripe_publishable_key,
        prices=prices.data,
    )

@app.post("/create_customer")
async def create_customer(item: Item, response: Response):
    try:
        # Create a new customer object
        customer = stripe.Customer.create(email=item.email)

        # At this point, associate the ID of the Customer object with your
        # own internal representation of a customer, if you have one.
        response.set_cookie(key="customer", value=customer.id)

        return {"customer": customer}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/create_subscription")
async def create_subscription(item: SubscriptionItem, request: Request):

    customer_id = request.cookies.get('customer')

    # Extract the price ID from environment variables given the name
    # of the price passed from the front end.
    #
    # `price_id` is the an ID of a Price object on your account.
    # This was populated using Price's `lookup_key` in the /config endpoint
    price_id = item.priceId

    try:
        subscription = stripe.Subscription.create(
            customer=item.customer_id,
            items=[{
                'price': price_id,
            }],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )
        return {"subscriptionId": subscription.id, "clientSecret": subscription.latest_invoice.payment_intent.client_secret}

    except Exception as e:
        raise HTTPException(status_code=400, detail=e.user_message)

@app.post("/cancel_subscription")
async def cancel_subscription(item: CancelItem):
    try:
        # Cancel the subscription by deleting it
        deletedSubscription = stripe.Subscription.delete(item.subscriptionId)
        return {"subscription": deletedSubscription}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
@app.get("/subscriptions")
async def list_subscriptions(request: Request):
    # Simulating authenticated user. Lookup the logged in user in your
    # database, and set customer_id to the Stripe Customer ID of that user.
    customer_id = request.cookies.get('customer')

    try:
        # Retrieve all subscriptions for given customer
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='all',
            expand=['data.default_payment_method']
        )
        return {"subscriptions": subscriptions}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/invoice_preview")
async def preview_invoice(request: Request, subscriptionId: Optional[str] = None, newPriceLookupKey: Optional[str] = None):
    # Simulating authenticated user. Lookup the logged in user in your
    # database, and set customer_id to the Stripe Customer ID of that user.
    customer_id = request.cookies.get('customer')

    try:
        # Retrieve the subscription
        subscription = stripe.Subscription.retrieve(subscriptionId)

        # Retrieve the Invoice
        invoice = stripe.Invoice.upcoming(
            customer=customer_id,
            subscription=subscriptionId,
            subscription_items=[{
                'id': subscription['items']['data'][0].id,
                'price': os.getenv(newPriceLookupKey),
            }],
        )
        return {"invoice": invoice}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/update_subscription")
async def update_subscription(item: UpdateItem):
    try:
        subscription = stripe.Subscription.retrieve(item.subscriptionId)

        update_subscription = stripe.Subscription.modify(
            item.subscriptionId,
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': os.getenv(item.newPriceLookupKey.upper()),
            }]
        )
        return {"update_subscription": update_subscription}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

# ElevenLabs API
@app.get("/elevenlabs/voices")
async def get_external_voices():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ELEVENLABS_API_URL)
            response.raise_for_status()  # Raise an HTTPError for bad responses
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return response.json()

# generate voice
@app.post("/elevenlabs_generate_voice/", response_class=StreamingResponse)
async def elevenlabs_generate_voice(
    text: str = Form(...),
    voice_id: str = Form(...),
):
    try:
        
        audio_generator = speech_synthesis.elevan_labs_client.generate(
            text=text,
            voice=Voice(
        voice_id=voice_id,
        settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, speaking_rate=0.8)
    )
        )
             
         # Convert the generator to bytes
        audio = b"".join(list(audio_generator))

        # Create a BytesIO stream from the audio bytes
        audio_stream = BytesIO(audio)

        headers = {
            'Content-Disposition': f'attachment; filename="{voice_id}.mp3"'
        }

        return StreamingResponse(audio_stream, media_type="audio/mpeg", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cloned voice
@app.post("/elevenlabs_clone_voice/", response_class=StreamingResponse)
async def elevenlabs_clone_voice(
    name: str = Form(...),
    description: str = Form(...),
    text: str = Form(...),
    voice_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    try:

        file_paths = []
        for file in files:
            file_location = f"/tmp/{file.filename}"
            with open(file_location, "wb") as buffer:
                buffer.write(file.file.read())
            file_paths.append(file_location)
        
        audio_generator = speech_synthesis.elevan_labs_client.clone(
            name=name,
            description=description,
            files=file_paths
        )

        # Clean up temporary files
        for file_path in file_paths:
            os.remove(file_path)

         # Convert the generator to bytes
        audio = b"".join(list(audio_generator))

        # Create a BytesIO stream from the audio bytes
        audio_stream = BytesIO(audio)

        headers = {
            'Content-Disposition': f'attachment; filename="{voice_id}.mp3"'
        }

        return StreamingResponse(audio_stream, media_type="audio/mpeg", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OpenAI API
# Text to Speech
@app.post("/open_ai_generate_voice/", response_class=StreamingResponse)
async def open_ai_generate_voice(
    text: str = Form(...),
    voice: str = Form(...),
):
    try:
        
        audio_generator = speech_synthesis.open_ai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

             
         # Convert the generator to bytes
        audio = b"".join(list(audio_generator))

        # Create a BytesIO stream from the audio bytes
        audio_stream = BytesIO(audio)

        headers = {
            'Content-Disposition': f'attachment; filename="{voice}.mp3"'
        }

        return StreamingResponse(audio_stream, media_type="audio/mpeg", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Speech to Text
@app.post("/open_ai_generate_text/")
async def open_ai_clone_voice(
    file: UploadFile = File(...)
):
    try:

        # Read the uploaded file
        audio_data = await file.read()

        # Save the audio file temporarily
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(audio_data)
        
        # Open the audio file for reading
        with open(temp_file_path, "rb") as audio_file:
            # Use OpenAI's Whisper model to transcribe the audio
            transcription = speech_synthesis.open_ai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                timestamp_granularities=["word"]
            )

        # Remove the temporary file
        os.remove(temp_file_path)

      

        return TranscriptionResponse(
            status="success",
            message="Transcription successful.",
            text=transcription['text']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Image Generation
@app.post("/generate_image/", response_model=ImageGenerationResponse)
async def generate_image(
    prompt: str = Form(...),
    size: str = Form("1024x1024"), 
    quality: str = Form("standard"), 
    n: int = Form(1)
):
    try:
        response = speech_synthesis.open_ai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )

        image_url = response.data[0].url

        return ImageGenerationResponse(
            status="success",
            message="Image generation successful.",
            image_url=image_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat Completion
@app.post("/chat_completion/", response_model=ChatCompletionResponse)
async def chat_completion(messages: List[Message], model: Optional[str] = "gpt-3.5-turbo"):
    try:

        response = speech_synthesis.open_ai_client.chat.completions.create(
            model=model,
            messages=[message.dict() for message in messages]
        )


        assistant_message = response.choices[0].message

        return ChatCompletionResponse(
            status="success",
            message="Chat completion successful.",
            response=assistant_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# MathPix API
@app.post("/mathpix_process_image/")
async def process_image(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        contents = await file.read()

        # Make a request to Mathpix API
        response = requests.post(
            "https://api.mathpix.com/v3/text",
            files={"file": (file.filename, contents, file.content_type)},
            data={
                "options_json": json.dumps({
                    "math_inline_delimiters": ["$", "$"],
                    "rm_spaces": True
                })
            },
            headers={
                "app_id": mathpix_api_id,
                "app_key": mathpix_api_key
            }
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Return the JSON response from Mathpix API
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mathpix_process_pdf/")
async def process_pdf(request: str):
    try:
        response = requests.post(
            "https://api.mathpix.com/v3/pdf",
            json={
                "url": request.url,
                "conversion_formats": {
                    "docx": True,
                    "tex.zip": True
                }
            },
            headers={
                "app_id": mathpix_api_id,
                "app_key": mathpix_api_key,
                "Content-type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/gmail/messages/")
# async def list_gmail_messages(email: str):
#     # if email not in users_db:
#     #     raise HTTPException(status_code=400, detail="User not registered.")
#     # token_file = users_db[email]
#     token_file = email
#     try:
#         creds = get_credentials(token_file)
#         service = build('gmail', 'v1', credentials=creds)
#         results = service.users().messages().list(userId='me').execute()
#         messages = results.get('messages', [])

#         if not messages:
#             return {"message": "No messages found."}
        
#         return {"messages": messages}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
# CORS Middleware
app = CORSMiddleware(
    app=app,
      allow_origins=[
        supertoken_config.app_info.website_domain, 
        "https://app.pandu.ai"
    ],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type"] + get_all_cors_headers(),
)

if __name__  == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)
