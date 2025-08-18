from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

# --- Google Docs setup ---
SCOPES = ["https://www.googleapis.com/auth/documents"]
SERVICE_ACCOUNT_FILE = "credentials.json"

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("docs", "v1", credentials=credentials)

DOCUMENT_ID = (
    "1tCHFb0rcnSntYHZgHFbZogPjadT42LFy1hz2nq4C_cM"  # replace with your document ID
)

# --- Load parsed LaTeX JSON ---
with open("bylaws.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# --- Helper functions ---
def insert_text_request(index, text):
    return {"insertText": {"location": {"index": index}, "text": text}}


def update_heading_request(start_index, end_index, level):
    return {
        "updateParagraphStyle": {
            "range": {"startIndex": start_index, "endIndex": end_index},
            "paragraphStyle": {"namedStyleType": f"HEADING_{level}"},
            "fields": "namedStyleType",
        }
    }


def create_list_item_request(start_index, end_index, nesting_level):
    """
    Create a numbered list item with proper indentation for nesting.
    nesting_level: 0 for top-level, 1 for first nested, etc.
    """
    print(start_index, end_index, nesting_level)
    return [
        # Apply numbered bullets once
        {
            "createParagraphBullets": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "bulletPreset": "NUMBERED_DECIMAL_NESTED",
            }
        },
        # Indentation for nesting
        {
            "updateParagraphStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "paragraphStyle": {
                    "indentFirstLine": {"magnitude": 0, "unit": "PT"},
                    "indentStart": {"magnitude": nesting_level * 18, "unit": "PT"}
                },
                "fields": "indentFirstLine,indentStart"
            }
        },
    ]


# --- Depth-first recursive generator ---
def generate_requests(nodes, index=1, list_level=0):
    requests = []

    for node in nodes:
        if node["type"] in ["section", "subsection", "subsubsection"]:
            text = node["title"] + "\n"
            requests.append(insert_text_request(index, text))
            level = {"section": 1, "subsection": 2, "subsubsection": 3}[node["type"]]
            requests.append(update_heading_request(index, index + len(text), level))
            index += len(text)
            # Depth-first recursion
            child_requests, index = generate_requests(
                node.get("children", []), index, list_level=0
            )
            requests += child_requests

        elif node["type"] == "enumerate":
            # Enumerate container: recurse into items at current list_level
            child_requests, index = generate_requests(
                node["items"], index, list_level=list_level + 1
            )
            requests += child_requests

        elif "text" in node:
            # Insert list item
            text = node["text"] + "\n"
            requests.append(insert_text_request(index, text))
            # Create numbered list with proper indentation
            requests += create_list_item_request(index, index + len(text), list_level)
            index += len(text)
            # Recurse into nested children with increased list_level
            child_requests, index = generate_requests(
                node.get("children", []), index, list_level + 1
            )
            requests += child_requests

        elif node["type"] == "text":
            # Plain paragraph text
            text = node["text"] + "\n"
            requests.append(insert_text_request(index, text))
            index += len(text)

    return requests, index


# --- Generate requests and send batchUpdate ---
requests, _ = generate_requests(data)

if requests:
    body = {"requests": requests}
    result = (
        service.documents().batchUpdate(documentId=DOCUMENT_ID, body=body).execute()
    )
    print("Document updated successfully!")
else:
    print("No requests generated.")
