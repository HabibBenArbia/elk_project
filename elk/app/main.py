from flask import Flask, request, render_template, jsonify
import os
from elasticsearch import Elasticsearch

app = Flask(__name__)
UPLOAD_FOLDER = '/app/data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ELASTICSEARCH_URL = "http://elasticsearch:9200"
INDEX_NAME = "csv_service"

# Initialize Elasticsearch client
es = Elasticsearch([ELASTICSEARCH_URL])

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 200

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        if not query:
            return render_template('search.html', query='', results=[])

        # Perform search in Elasticsearch with a bool query
        search_query = {
            "query": {
                "bool": {
                    "should": [
                        # Match query for text fields (IMEI, Status)
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["IMEI", "Status"]  # Full-text fields
                            }
                        },
                        # Term query for exact match on Username.keyword (exact match for strings)
                        {
                            "term": {
                                "Username.keyword": query  # Exact match for Username
                            }
                        }
                    ],
                    "minimum_should_match": 1  # Ensure at least one condition must match
                }
            },
            "collapse": {
                "field": "ID"  # Collapse results based on the ID field to remove duplicates
            },
            "size": 100  # Limit the number of results
        }

        try:
            response = es.search(index=INDEX_NAME, body=search_query)
            hits = response.get('hits', {}).get('hits', [])
            return render_template('search.html', query=query, results=hits)
        except Exception as e:
            print("Elasticsearch error:", e)
            return jsonify({'error': str(e), 'query': search_query}), 500

    return render_template('search.html', query='', results=[])








if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
