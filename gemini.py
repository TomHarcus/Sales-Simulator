from google import genai
from google.genai import types
from session import Session, Turn

client = genai.Client()

def get_response(user_session, user_message):
    
    # gemini prompt
    instruction = f"""
    You are acting as a customer with certain parameters with a seller who is practicing and looking to improve their
    selling skills and techniques. In this simulation, you need to raise objections, adapt your resistance based on current
    interest level, do not fold to easily, and behave like a realistic B2B customer.

    The following are your set parameters and you should act out this simulation based on their values: You are currently set to 
    {user_session.customer_type.value} where your responses must reflect that customer difficulty level. Your personality type is 
    {user_session.personality}, once again your responses must reflect this type. The scenario context is {user_session.description}
    and your customers persona current interest level is {user_session.interest_level} out of 5.

    For your response, return it in JSON format. Your response JSON should include the content of your simulated response and the updated 
    interest level. You decided what the interest level should be set to based on the interaction, make it as realistic as possible. the interest
    level is bounded between 1 and 5.
    """

    # get current turn
    current_turn = Turn("user", [user_message.content])

    # get contents
    content = user_session.history.copy()
    content.append(current_turn)

    # format content into gemini form
    formatted_content = [x.__dict__ for x in content]

    # pass data to gemini
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=instruction),
        contents=formatted_content
    )

    print(response.text)