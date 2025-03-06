from flask import Flask, request, jsonify, render_template
import openai
import time
import os
from flask_cors import CORS
from dotenv import load_dotenv

# Load API key from tes.env
load_dotenv(".env")  # Specify your env file

app = Flask(__name__)
CORS(app)  # Enable CORS

# Check if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Check your .env file!")

client = openai.OpenAI(api_key=api_key)
ASSISTANT_ID = "asst_RX53rRJGq5G78TZqPjHUNN2B"



@app.route("/")
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in request"}), 400

        user_input = data["message"]

        # Create a thread
        thread = client.beta.threads.create()

        # Send user message
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_input
        )

        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=ASSISTANT_ID
        )

        # Wait until completion
        import time

        # Keep checking until OpenAI finishes replying
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":  # If OpenAI has finished responding, stop waiting
                break
            time.sleep(1)  # Wait 1 second before checking again

        # time.sleep(3)

       # Fetch response messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Debugging: Print messages to see the full response
        print("Full messages response:", messages.data)

        if not messages.data:
            return jsonify({"error": "No response from assistant"}), 500

        # Check the structure of messages before extracting response_text
        for msg in messages.data:
            print("Message Role:", msg.role)  # Should print "assistant" or "user"
            print("Message Content:", msg.content)

         # Extract assistant's response while ignoring file attachments
        response_text = None
        for msg in reversed(messages.data):  # Start from the latest message
            if msg.role == "assistant":
                print("Assistant Message Content:", msg.content)  # Debugging print

                # Loop through all possible content parts
                for content in msg.content:
                    if hasattr(content, "text") and hasattr(content.text, "value"):
                        response_text = content.text.value

                        # Remove unwanted file references from the text
                        response_text = response_text.split("【")[0].strip()
                        break  # Stop once we get a valid text response
                    
                    elif hasattr(content, "file_ids") and content.file_ids:  
                        print("Ignoring file response:", content.file_ids)  # Debugging print
                        continue  # Skip file attachments
                
            if response_text:  
                break  # Stop once a valid text response is found


        # If no assistant response found, return an error
        if response_text is None:
            return jsonify({"error": "Assistant did not respond"}), 500

        return jsonify({"response": response_text})


    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
