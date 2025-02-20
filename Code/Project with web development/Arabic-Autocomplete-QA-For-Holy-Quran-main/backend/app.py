from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from models import load_data, create_frequency_dict, AutocompleteApp, extract_words
#import tensorflow as tf



app = Flask(__name__)
CORS(app, supports_credentials=True)


# Load your data
file_path1 = 'NLP_Project.xlsx'
file_path2 = 'AAQQAC.xlsx'
aya_file = 'uthmani-simple-qurancom.md'
tafseer_file = 'ar-mokhtasar-islamhouse.md'

data = load_data(file_path1, file_path2, aya_file, tafseer_file)
data['q'] = data['Question'].astype(str)
data['a'] = data['Answer'].astype(str)



# Create frequency dictionary from the loaded questions
freq_dict = create_frequency_dict(data)


# Initialize AutocompleteApp
dictionary = extract_words(data)
autocomplete_app = AutocompleteApp(freq_dict, dictionary, data)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route('/popular-questions', methods=['GET'])
def popular_questions():
    try:
        with open('popular_questions.json', 'r', encoding='utf-8') as file:
            questions = json.load(file)
        return jsonify(questions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/autocomplete', methods=['GET'])
def autocomplete_endpoint():
    try:
        query = request.args.get('query', '')
        app.logger.debug(f"Received query: {query}")
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        print(query)
        suggestions = autocomplete_app.get_suggestions(query)
        app.logger.debug(f"Suggestions: {suggestions}")
        
        # Ensure the suggestions are in a proper list format
        if isinstance(suggestions, list):
            return jsonify(suggestions)
        else:
            return jsonify({"error": "Internal processing error"}), 500
    except Exception as e:
        app.logger.error(f"Error occurred: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/search', methods=['GET'])
def search_endpoint():
    query = request.args.get('query', '')
    results = autocomplete_app.submit_query(query)
    return jsonify(results)


@app.route('/correction', methods=['GET'])
def correction_endpoint():
    query = request.args.get('query', '')
    corrected_text = autocomplete_app.accept_correction(query)
    return jsonify({"corrected_text": corrected_text})


if __name__ == "__main__":
    app.run(debug=True)
