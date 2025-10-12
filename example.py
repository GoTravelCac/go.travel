# By Nandish
                  # Uncomment this when we want to save our file
# %%writefile app.py
import os
import re
import google.generativeai as genai
import time
import random

# Try Colab first, otherwise fall back to dotenv
try:
    from google.colab import userdata
    IS_COLAB = True
except ImportError:
    import dotenv
    dotenv.load_dotenv()
    IS_COLAB = False

# Set up Loading bar
total = 98

# 0. Title
print("-" * 101)
print("-----                                         go.travel                                         -----")
print("-----                                AI Travel Itinerary Planner                                -----")
print("-" * 101)
print("\n\n")
time.sleep(5)

# 1. Set up API access (single key)
api_key = "AIzaSyAzvLtQnLLpKhS45VovdLr6-cZDAAyJmuc"


# Uncomment this below?
# api_key = None
# if IS_COLAB:
#     try:
#         # api_key = userdata.get('GOOGLE_API_KEY')
#     except userdata.SecretNotFoundError:
#         pass
# else:
#     # api_key = os.getenv('GOOGLE_API_KEY')

# Configure Gemini with the key
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        gemini_model = None
else:
    gemini_model = None

# 2. Gather user input
print("-" * 100)
print("---                                     Gathering user input                                     ---\n")
time.sleep(2)

def get_travel_preferences():
    """Collects user input for travel preferences."""
    destination = input("Where would you like to go? ")
    start_date = input("When do you want to start your trip (MM/DD/YY)? ")
    end_date = input("When do you want to end your trip (MM/DD/YY)? ")
    duration = input("How long will your trip be (in days)? ")
    interests = input("What are your interests or desired activities (e.g., historical sites, food, adventure)? ")

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "duration": duration,
        "interests": interests,
    }

user_preferences = get_travel_preferences()
print("\n---                                  Collected user preferences                                  ---")
print()
print("-" * 100)
time.sleep(2)

# 3. Itinerary generation
print("\n---                               Generating Preliminary Itinerary                               ---")
def generate_itinerary_with_gemini(preferences, model):
    """Generates a preliminary travel itinerary using the Gemini API."""
    if model is None:
        return "Gemini API key not set or model initialization failed. Could not generate itinerary."

    prompt = f"""Generate a travel itinerary for a trip to {preferences['destination']} from {preferences['start_date']} to {preferences['end_date']} (duration: {preferences['duration']} days). The user is interested in: {preferences['interests']}.

    Please provide a detailed day-by-day itinerary including activities, potential places to visit, and consider the user's interests. Format the output as a clear, easy-to-read text itinerary. Do not include any *, **, or # characters, use indents, hyphens, and em dashes for clearer formatting.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred while generating the itinerary: {e}")
        return "Could not generate itinerary."

itinerary = generate_itinerary_with_gemini(user_preferences, gemini_model)


# 4. Add Waiting
time.sleep(5)
print("\n---                               Preliminary Itinerary Generated                                ---")
time.sleep(2)

print("\n---                                     Enhancing itinerary                                      ---")
# Remove unwanted characters from the enhanced itinerary
itinerary = re.sub(r'[*\#]', '', itinerary)

time.sleep(5)
print("\n---                                 Enhanced Itinerary Generated                                 ---")
time.sleep(2)
print("\n---                                      Loading Itinerary                                       ---")
print()
time.sleep(3)

print("[", end="", flush=True)
for i in range(total):
  time.sleep((random.random())/10)
  print('█', sep='\r', end='')
print("]", end="")
time.sleep(2)
print()
print()
time.sleep(1)
print("-" * 100)
print()
print(itinerary)
print("-" * 100)
print()

# 5. Allow for feedback and iteration
time.sleep(5)
print("---                                    Feedback and Iteration                                    ---")
time.sleep(2)

# ✅ Always start feedback loop with the most recent valid itinerary
current_itinerary_for_feedback = itinerary

def get_feedback():
    """Asks the user for feedback on the itinerary."""
    feedback = input("\nWould you like to provide feedback on this itinerary? (yes/no): ").lower()
    if feedback == 'yes':
        return input("Please provide your feedback: ")
    else:
        return None

def refine_itinerary_with_feedback(preferences, current_itinerary, feedback, model):
    """Refines the Gemini prompt based on user feedback."""
    refined_prompt = f"""The user previously requested an itinerary for a trip to {preferences['destination']} from {preferences['start_date']} to {preferences['end_date']}, lasting {preferences['duration']} days, with interests in: {preferences['interests']}.
This was the generated itinerary:
---
{current_itinerary}
---
The user has provided the following feedback: "{feedback}".

Please generate an UPDATED itinerary based on the original preferences and the user's feedback. Focus on addressing the user's comments and making necessary adjustments. Provide a detailed day-by-day itinerary as before. Do not include any *, **, ## or # characters, use indents, hyphens, and em dashes for clearer formatting.
"""
    return refined_prompt

max_feedback_iterations = 3
iteration = 0

while iteration < max_feedback_iterations:
    # print("\n--- Current Itinerary for Feedback ---")
    display_itinerary = current_itinerary_for_feedback if current_itinerary_for_feedback and current_itinerary_for_feedback != "Could not generate itinerary." else current_itinerary_for_feedback
    # print(display_itinerary)

    if current_itinerary_for_feedback == "Could not generate itinerary." or gemini_model is None:
        print("       Cannot proceed with feedback loop as itinerary generation failed or API key is missing.      ")
        break

    user_feedback = get_feedback()

    if user_feedback is None:
        print()
        print("-" * 100)
        for i in range(10):
          print()
        break

    print()
    print("-" * 100)
    print("\n                           Applying feedback and regenerating itinerary...                          ")
    time.sleep(2)
    print()
    time.sleep(2)
    print("[", end="", flush=True)
    for i in range(total):
      time.sleep((random.random())/15)
      print('█', sep='\r', end='')
    print("]", end="")
    time.sleep(2)
    print()
    print()
    print("-" * 100)
    print()

    # Pass the gemini_model to the refine_itinerary_with_feedback function call
    refined_prompt = refine_itinerary_with_feedback(user_preferences, current_itinerary_for_feedback, user_feedback, gemini_model)

    try:
        # Call generate_content with the refined prompt
        response = gemini_model.generate_content(refined_prompt)
        # Update the current_itinerary_for_feedback with the new response
        current_itinerary_for_feedback = response.text
        updated_itinerary = re.sub(r'[*\#]', '', current_itinerary_for_feedback)
        time.sleep(2)
        print("\n---                                      Updated Itinerary                                       ---")
        time.sleep(2)
        print()
        print(updated_itinerary)
        print("-" * 100)



    except Exception as e:
        print(f"An error occurred while regenerating the itinerary: {e}")
        updated_itinerary = "Could not regenerate itinerary."

    iteration += 1
    if iteration == max_feedback_iterations:
        print("\n                              Maximum feedback iterations reached                              ")
        print("\n"*10)
        time.sleep(3)

print("-" * 100)
print("----------                                 Final Itinerary                                ----------")
print("-" * 100)
print()
final_display_itinerary = current_itinerary_for_feedback if current_itinerary_for_feedback and current_itinerary_for_feedback != "Could not generate itinerary." else itinerary
print(final_display_itinerary)
print("-" * 100)
time.sleep(5)

# 6. Finish task
print("---                                         Task Finished                                        ---")
print("\n                                The itinerary generation is complete                                ")
time.sleep(2)
print("                                          Come back again!                                          ")