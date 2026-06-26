from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from session import Session, Customer_Type
import secrets
from gemini import get_response
from model import classify, tokenize
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


limiter = Limiter(key_func=lambda request: request.client.host)

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# all active sessions
sessions_dict = {}

# schema for a session
class UserSession(BaseModel):
    description : str
    personality : str
    customer_type : Customer_Type
    interest_level : int

# schema for a message
class Message(BaseModel):
    session_id : str
    content : str

# schema for session id
class SessionID(BaseModel):
    session_id : str

# initialise session endpoint
@app.post("/start")
async def start_session(user_session: UserSession):
    # generate unique session id
    user_session_id = secrets.token_hex(16)

    user_session = Session(user_session.description, user_session.personality, user_session.customer_type, user_session.interest_level)

    # connect session id to user session class
    sessions_dict[user_session_id] = user_session
    return user_session_id

# message endpoint
@app.post("/message")
@limiter.limit("30/minute")
async def get_message(request: Request, user_message: Message):
    # check if session exists
    if user_message.session_id in sessions_dict:
        user_session = sessions_dict[user_message.session_id]
    else:
        raise HTTPException(status_code=404, detail="Session not found")
    
    threshold = 0.65
    low_confidence = False
    distribution = None
    classification = ("N/A", 0)
    if user_session.get_counter() > 0 and len(user_message.content) >= 20:
        model_input = tokenize(user_session.get_previous_message(), user_message.content)
        distribution = classify(model_input)

        for i in distribution:
            distribution[i] = round(distribution[i], 2)

        list_distribution = distribution.items()

        classification = max(list_distribution, key=lambda x: x[1])

        if classification[1] < threshold:
            low_confidence = True
            user_session.update_low_confidence()
     


    response = get_response(user_session, user_message)

    user_session.update_counter()
    user_session.update_interest_level(response["interest_level"])
    user_session.update_history("user", user_message.content)
    content = response["content"]
    user_session.update_history("model", content)
    user_session.update_objections(response["objection"])
    user_session.update_classification_history(classification[0])

    if len(user_message.content) < 20:
        return {
            "content": content, 
            "distribution": distribution, 
            "classification": "N/A", 
            "low_confidence": False, 
            "objection": response["objection"], 
            "turn_number": user_session.counter,
            "interest_level": user_session.interest_level,
            "length_valid": False
        }


    return {
        "content": content, 
        "distribution": distribution, 
        "classification": classification[0], 
        "low_confidence": low_confidence, 
        "objection": response["objection"], 
        "turn_number": user_session.counter,
        "interest_level": user_session.interest_level,
        "length_valid": True
        }


@app.post("/end")
async def end_session(user_session_id : SessionID):
    # remove users session from dictionary
    try:
        user_session = sessions_dict[user_session_id.session_id]

        description = user_session.description
        personality = user_session.personality
        difficulty = user_session.customer_type

        interest_trajectory = user_session.interest_trajectory

        classification_history = user_session.classification_history
        if (len(classification_history) > 0 and len(interest_trajectory) > 0):
            classification_counter = Counter(classification_history)
            most_frequent_class = classification_counter.most_common(1)[0]

            final_interest_level = user_session.interest_trajectory[-1]
        else:
            most_frequent_class = ("N/A", 0)
            final_interest_level = "N/A"

        low_confidence_count = user_session.low_confidence_count

        total_turns = user_session.counter

        del sessions_dict[user_session_id.session_id]

        return {
            "description": description,
            "personality": personality,
            "difficulty": difficulty,
            "interest_trajectory": interest_trajectory,
            "final_interest_level": final_interest_level,
            "classification_history": classification_history,
            "most_frequent_class": most_frequent_class,
            "low_confidence_count": low_confidence_count,
            "total_turns": total_turns
        }
    
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    
