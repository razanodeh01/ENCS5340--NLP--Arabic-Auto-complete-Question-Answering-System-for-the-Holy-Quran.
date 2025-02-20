import pandas as pd
from collections import defaultdict
import re
import Levenshtein as lev

stop_words = set(["ما", "هو", "اذكر", "هي", "في", "من", "إلى", "على", "عن", "أن", "إن", "قد", "هل", "ل", "التي", "الذي", "الذين", "اللاتي", "اللاتي", "اللائي","هم"])

def load_markdown_data(aya_file, tafseer_file):
    # Read the contents of the files
    with open(aya_file, 'r', encoding='utf-8') as f:
        aya_content = f.read()
        
    with open(tafseer_file, 'r', encoding='utf-8') as f:
        tafseer_content = f.read()

    # Split content into sections based on the pattern '# number'
    aya_sections = re.split(r'\n# \d+\n', aya_content)
    tafseer_sections = re.split(r'\n# \d+\n', tafseer_content)

    # Ensure the first element is discarded if it's empty
    if aya_sections[0].strip() == '':
        aya_sections = aya_sections[1:]
    if tafseer_sections[0].strip() == '':
        tafseer_sections = tafseer_sections[1:]

    # Extract verses and explanations
    data = []
    for aya, tafseer in zip(aya_sections, tafseer_sections):
        verse_text = aya.strip()
        tafseer_text = tafseer.strip()
        
        if verse_text and tafseer_text:
            data.append({
                'Question': verse_text,
                'Answer': tafseer_text
            })

    return pd.DataFrame(data)

def load_data(file_path1, file_path2, aya_file, tafseer_file):
    data1 = pd.read_excel(file_path1)
    data2 = pd.read_excel(file_path2, usecols=['Question', 'Answer'])
    markdown_data = load_markdown_data(aya_file, tafseer_file)
    data = pd.concat([data1, data2, markdown_data], ignore_index=True)

    print(f"Loaded {len(data)} questions with duplicates.")

    # Remove duplicate questions
    data = data.drop_duplicates(subset=['Question'])

    print(f"Loaded {len(data)} questions.")
    print(data.head())

    return data


def preprocess(text):
    # Remove Arabic diacritics (حركات التشكيل)
    diacritics = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = diacritics.sub('', text)

    # Replace different forms of "ا"
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')

    # Normalize specific words
    text = text.replace('التى', 'التي')

    # Additional normalization rules
    text = text.replace('\u0649', '\u064A')  # Replace 'ى' (U+0649) with 'ي' (U+064A)
    text = text.replace('\u0624', '\u0621')  # Replace 'ؤ' (U+0624) with 'ء' (U+0621)
    text = text.replace('\u0626', '\u0621')  # Replace 'ئ' (U+0626) with 'ء' (U+0621)
    text = text.replace('\u0629', '\u0647')  # Replace 'ة' (U+0629) with 'ه' (U+0647)

    # Remove the Arabic definite article "ال"
    text = re.sub(r'\bال', '', text)

    # Remove punctuation and non-word characters
    text = re.sub(r'[^\w\s]', '', text)

    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Convert to lowercase (not necessary for Arabic but useful for mixed content)
    text = text.lower()

    return text


def extract_words(data):
    combined_text = ' '.join(data['q'].astype(str)) + ' ' + ' '.join(data['a'].astype(str))
    words = set(preprocess(combined_text).split())
    return words


def create_frequency_dict(data):
    freq_dict = defaultdict(list)
    for entry in data['Question']:
        original_text = entry  # Store the original text
        processed_entry = preprocess(entry)
        freq_dict[processed_entry].append(original_text)
    return freq_dict



def autocomplete(input_text, freq_dict):
    input_text = preprocess(input_text)
    suggestions = {}
    for processed_text, original_texts in freq_dict.items():
        if processed_text.startswith(input_text):
            for original_text in original_texts:
                suggestions[original_text] = suggestions.get(original_text, 0) + 1
    
    sorted_suggestions = dict(sorted(suggestions.items(), key=lambda item: item[1], reverse=True))
    return sorted_suggestions


def generate_ngrams(text, n):
    words = text.split()
    # Generate n-grams from complete phrases instead of just words
    ngrams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    return ngrams


def weighted_jaccard_similarity(str1, str2, stop_words_weight=0.3):
    a = set(str1.split())
    b = set(str2.split())
    intersection = a.intersection(b)
    union = a.union(b)
    
    intersection_weighted_sum = sum([stop_words_weight if word in stop_words else 1.0 for word in intersection])
    union_weighted_sum = sum([stop_words_weight if word in stop_words else 1.0 for word in union])
    
    return float(intersection_weighted_sum) / union_weighted_sum

def find_closest_questions(input_text, data, n=3):
    input_text = preprocess(input_text)
    input_ngrams = generate_ngrams(input_text, n)
    input_ngrams = ' '.join(input_ngrams)

    def calculate_similarity(question):
        question_ngrams = generate_ngrams(preprocess(question), n)
        question_ngrams = ' '.join(question_ngrams)
        return weighted_jaccard_similarity(input_ngrams, question_ngrams)
    
    if len(input_text.split()) < n:
        data['similarity'] = data['q'].apply(lambda question: weighted_jaccard_similarity(preprocess(question), input_text))
    else:
        data['similarity'] = data['q'].apply(calculate_similarity)

    closest_matches = data.sort_values(by='similarity', ascending=False).head(10)
    return closest_matches[['q', 'a']]


class ArabicSpellChecker:
    def __init__(self, dictionary):
        self.dictionary = set(dictionary)

    def is_misspelled(self, word):
        return word not in self.dictionary

    def correct_word(self, word):
        if self.is_misspelled(word):
            return min(self.dictionary, key=lambda x: lev.distance(word, x))
        return word

class AutocompleteApp:
    def __init__(self, freq_dict, dictionary, data):
        self.data = data  # Pass the entire DataFrame
        self.freq_dict = freq_dict
        self.spell_checker = ArabicSpellChecker(dictionary)


    def accept_correction(self, user_input):
        if user_input.startswith("Did you mean:"):
            corrected_text = user_input.split(": ", 1)[1]
            corrected_text = corrected_text[:-1]
            return corrected_text
        return user_input

    def submit_query(self, user_input):
        if user_input.strip() == "":
            return {"message": "Please enter a question."}

        suggestions = find_closest_questions(user_input, self.data)
        if suggestions.empty:
            return {"message": "No matching question found."}
        else:
            first_match = suggestions.iloc[0]
            return {
                "best_match": first_match['q'],
                "answer": first_match['a'],
                "matches": suggestions.to_dict(orient='records')
            }

    def on_listbox_select(self, selected_text):
        return selected_text

    def handle_key_release(self, user_input):
        if user_input.endswith(' '):
            return self.suggest_correction(user_input)
        return self.get_suggestions(user_input)

    def get_suggestions(self, text):
        text = text.strip()
        if text and text[-1] != ' ':
            words = text.split()
            corrected_words = []
            for word in words:
                word = preprocess(word)
                if self.spell_checker.is_misspelled(word):
                    corrected_words.append(self.spell_checker.correct_word(word))
                    print(f"Corrected word: {corrected_words[-1]} for {word}")
                else:
                    corrected_words.append(word)

            corrected_text = ' '.join(corrected_words)
            suggestions = autocomplete(corrected_text, self.freq_dict)

            corrected_words[-1] = words[-1]
            corrected_text = ' '.join(corrected_words)
            suggestions2 = autocomplete(corrected_text, self.freq_dict)
            suggestions_plus = find_closest_questions(corrected_text, self.data)

            combined_suggestions = list(suggestions.keys()) + list(suggestions2.keys())

            if len(combined_suggestions) < 10:
                print("********************************************")
                unique_plus_suggestions2 = []
                for idx, row in suggestions_plus.iterrows():
                    suggestion = row['q']
                    if suggestion not in combined_suggestions:
                        unique_plus_suggestions2.append(suggestion)
                        if len(combined_suggestions) + len(unique_plus_suggestions2) >= 10:
                            break
                combined_suggestions = combined_suggestions + unique_plus_suggestions2

            # remove duplicates
            combined_suggestions = list(dict.fromkeys(combined_suggestions))

            # Limit to top 10 suggestions            
            final_suggestions = combined_suggestions[:10]
            print(f"Final combined suggestions: {final_suggestions}")
            return final_suggestions
        return []

    def suggest_correction(self, user_input):
        text = user_input.strip()
        if not text:
            return {}

        words = text.split()
        corrected_words = []
        corrections_made = False
        for word in words:
            if self.spell_checker.is_misspelled(word):
                corrected_word = self.spell_checker.correct_word(word)
                corrected_words.append(corrected_word)
                if corrected_word != word:
                    corrections_made = True
            else:
                corrected_words.append(word)

        corrected_text = ' '.join(corrected_words)
        if corrections_made:
            return {"suggestion": f"Did you mean: {corrected_text}?"}
        else:
            return {}




