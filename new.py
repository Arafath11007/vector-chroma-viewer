from flask import Flask, jsonify, request, render_template_string
import chromadb
from chromadb.config import Settings
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration - Update these
CHROMA_HOST = "13.202.22.145"
CHROMA_PORT = 8000

# Initialize ChromaDB client
client = chromadb.HttpClient(
    host=CHROMA_HOST, port=CHROMA_PORT, settings=Settings(allow_reset=False)
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromaDB Viewer</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect } = React;

        function App() {
            const [collections, setCollections] = useState([]);
            const [selectedCollection, setSelectedCollection] = useState('');
            const [documents, setDocuments] = useState([]);
            const [filteredDocs, setFilteredDocs] = useState([]);
            const [searchTerm, setSearchTerm] = useState('');
            const [filters, setFilters] = useState({});
            const [loading, setLoading] = useState(false);
            const [selectedDoc, setSelectedDoc] = useState(null);

            useEffect(() => {
                fetchCollections();
            }, []);

            useEffect(() => {
                if (selectedCollection) {
                    fetchDocuments();
                }
            }, [selectedCollection]);

            useEffect(() => {
                applyFilters();
            }, [documents, searchTerm, filters]);

            const fetchCollections = async () => {
                try {
                    const res = await fetch('/api/collections');
                    const data = await res.json();
                    setCollections(data.collections);
                } catch (err) {
                    console.error('Error fetching collections:', err);
                }
            };

            const fetchDocuments = async () => {
                setLoading(true);
                try {
                    const res = await fetch(`/api/collection/${selectedCollection}`);
                    const data = await res.json();
                    setDocuments(data.documents);
                } catch (err) {
                    console.error('Error fetching documents:', err);
                } finally {
                    setLoading(false);
                }
            };

            const applyFilters = () => {
                let filtered = documents;

                // Search filter
                if (searchTerm) {
                    filtered = filtered.filter(doc => {
                        const searchIn = JSON.stringify(doc).toLowerCase();
                        return searchIn.includes(searchTerm.toLowerCase());
                    });
                }

                // Metadata filters
                Object.entries(filters).forEach(([key, value]) => {
                    if (value) {
                        filtered = filtered.filter(doc => {
                            const metaValue = doc.metadata?.[key];
                            return metaValue?.toString().toLowerCase().includes(value.toLowerCase());
                        });
                    }
                });

                setFilteredDocs(filtered);
            };

            const getMetadataKeys = () => {
                if (documents.length === 0) return [];
                const keys = new Set();
                documents.forEach(doc => {
                    if (doc.metadata) {
                        Object.keys(doc.metadata).forEach(k => keys.add(k));
                    }
                });
                return Array.from(keys);
            };

            const truncate = (str, len = 100) => {
                if (!str) return '';
                return str.length > len ? str.substring(0, len) + '...' : str;
            };

            return (
                <div className="min-h-screen p-6">
                    <div className="max-w-7xl mx-auto">
                        {/* Header */}
                        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                            <h1 className="text-3xl font-bold text-gray-800 mb-2">ChromaDB Viewer</h1>
                            <p className="text-gray-600">Browse and search your vector database</p>
                        </div>

                        {/* Collection Selector */}
                        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Collection
                            </label>
                            <select
                                value={selectedCollection}
                                onChange={(e) => setSelectedCollection(e.target.value)}
                                className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value="">-- Choose a collection --</option>
                                {collections.map(col => (
                                    <option key={col} value={col}>{col}</option>
                                ))}
                            </select>
                            {selectedCollection && (
                                <p className="mt-2 text-sm text-gray-600">
                                    {documents.length} documents found
                                </p>
                            )}
                        </div>

                        {selectedCollection && (
                            <>
                                {/* Search and Filters */}
                                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Search
                                        </label>
                                        <input
                                            type="text"
                                            placeholder="Search in all fields..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                    </div>

                                    {/* Metadata Filters */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Filter by Metadata
                                        </label>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                            {getMetadataKeys().slice(0, 6).map(key => (
                                                <input
                                                    key={key}
                                                    type="text"
                                                    placeholder={`Filter by ${key}...`}
                                                    value={filters[key] || ''}
                                                    onChange={(e) => setFilters({...filters, [key]: e.target.value})}
                                                    className="px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            ))}
                                        </div>
                                        {searchTerm || Object.values(filters).some(v => v) ? (
                                            <button
                                                onClick={() => { setSearchTerm(''); setFilters({}); }}
                                                className="mt-3 text-sm text-blue-600 hover:text-blue-800"
                                            >
                                                Clear all filters
                                            </button>
                                        ) : null}
                                    </div>
                                </div>

                                {/* Results */}
                                {loading ? (
                                    <div className="text-center py-12">
                                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
                                        <p className="mt-2 text-gray-600">Loading documents...</p>
                                    </div>
                                ) : (
                                    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                                        <div className="p-4 bg-gray-50 border-b">
                                            <p className="text-sm font-medium text-gray-700">
                                                Showing {filteredDocs.length} of {documents.length} documents
                                            </p>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full">
                                                <thead className="bg-gray-100 border-b">
                                                    <tr>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">ID</th>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Content</th>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Metadata</th>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-200">
                                                    {filteredDocs.map((doc, idx) => (
                                                        <tr key={idx} className="hover:bg-gray-50">
                                                            <td className="px-4 py-3 text-sm font-mono text-gray-900">
                                                                {truncate(doc.id, 30)}
                                                            </td>
                                                            <td className="px-4 py-3 text-sm text-gray-700">
                                                                {truncate(doc.content, 80)}
                                                            </td>
                                                            <td className="px-4 py-3 text-sm">
                                                                <div className="flex flex-wrap gap-1">
                                                                    {Object.entries(doc.metadata || {}).slice(0, 3).map(([k, v]) => (
                                                                        <span key={k} className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                                                            {k}: {truncate(String(v), 20)}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <button
                                                                    onClick={() => setSelectedDoc(doc)}
                                                                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                                                >
                                                                    View
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                            {filteredDocs.length === 0 && (
                                                <div className="text-center py-12 text-gray-500">
                                                    No documents match your filters
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    {/* Document Detail Modal */}
                    {selectedDoc && (
                        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedDoc(null)}>
                            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                                <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
                                    <h3 className="text-lg font-semibold">Document Details</h3>
                                    <button onClick={() => setSelectedDoc(null)} className="text-gray-500 hover:text-gray-700">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                                <div className="p-6 space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">ID</label>
                                        <p className="p-3 bg-gray-50 rounded font-mono text-sm break-all">{selectedDoc.id}</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                                        <p className="p-3 bg-gray-50 rounded text-sm whitespace-pre-wrap">{selectedDoc.content}</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Metadata</label>
                                        <pre className="p-3 bg-gray-50 rounded text-xs overflow-x-auto">{JSON.stringify(selectedDoc.metadata, null, 2)}</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/collections")
def get_collections():
    try:
        collections = client.list_collections()
        return jsonify({"collections": [col.name for col in collections]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/collection/<name>")
def get_collection_docs(name):
    try:
        collection = client.get_collection(name)
        count = collection.count()

        results = collection.get(limit=count if count > 0 else 1)

        documents = []
        for i in range(len(results["ids"])):
            documents.append(
                {
                    "id": results["ids"][i],
                    "content": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "embedding_dim": (
                        len(results["embeddings"][i])
                        if results.get("embeddings") and results["embeddings"][i]
                        else 0
                    ),
                }
            )

        return jsonify({"documents": documents, "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("ChromaDB Viewer - Web Interface")
    print("=" * 60)
    print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
    print("\nStarting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
