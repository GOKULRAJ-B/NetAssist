from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import google.generativeai as genai
import os
import markdown

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


ALLOWED_USERS = {
    "Gokul": "hi",
    "Piyush": "hi1",
    "Priyamshu": "hi2"
}

def update_prompt_history(prompt):
    history = session.get('prompt_history', [])
    history.append(prompt)
    session['prompt_history'] = history[-5:] 
    session.modified = True

def get_gemini_response(user_message):
    history = session.get('prompt_history', [])
    
    if history:
        prompt_text = (
            "Here are some previous networking questions the user asked:\n"
            + "\n".join(history[:-1])
            + "\n\nNow answer the current question clearly:\n" + user_message
        )
    else:
        prompt_text = user_message

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        system_instruction=(
            "You are a professional networking assistant. You must only respond to questions strictly related to computer networking. "
            "If the user asks about anything outside this topic (like food, movies, etc.), reply with: "
            "if user inputs hello say hi and ask for networking questions"
            "Sorry, I can only assist with networking-related questions.'"
        )
    )

    convo = model.start_chat(history=[])
    response = convo.send_message(prompt_text)

    html_response = markdown.markdown(response.text)
    return html_response

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in ALLOWED_USERS and ALLOWED_USERS[username] == password:
            session["username"] = username
            return redirect(url_for("chat"))
        else:
            error = "Invalid username or password."
            return render_template("login.html", error=error)

    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return render_template("chat.html")

    user_message = request.json.get("message")
    if user_message:
        bot_response = get_gemini_response(user_message)
        if "Sorry, I can only assist with networking-related questions." not in bot_response:
            update_prompt_history(user_message)
        return jsonify({"response": bot_response})

    return jsonify({"response": "Sorry, I didn't understand that."})

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    user_feedback = request.json.get("feedback")
    user_message = request.json.get("message")

    print(f"Received feedback: {user_feedback}, Received message: {user_message}")

    if user_feedback and user_message:
        try:
            with open("feedback.txt", "a") as file:
                file.write(f"Message: {user_message}\nFeedback: {user_feedback}\n\n")
            return jsonify({"status": "success", "message": "Thank you for your feedback!"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error saving feedback: {str(e)}"})
    else:
        print(f"Invalid feedback: {user_feedback}, Invalid message: {user_message}")
        return jsonify({"status": "error", "message": "Invalid feedback."})

@app.route("/clear_history")
def clear_history():
    session.pop('prompt_history', None)
    return "Prompt history cleared."

if __name__ == "__main__":
    app.run(debug=True)
