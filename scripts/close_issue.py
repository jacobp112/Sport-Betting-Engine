import urllib.request
import json
import os
import ssl

ssl_context = ssl._create_unverified_context()
TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "jacobp112/Sport-Betting-Engine"

def github_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python"
    }
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, method=method, data=req_data)
    with urllib.request.urlopen(req, context=ssl_context) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    url = f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100"
    issues = github_request(url)
    data1_issue = next((i for i in issues if i['title'].startswith("DATA-1 ")), None)
    
    if not data1_issue:
        print("DATA-1 issue not found!")
        return
        
    issue_num = data1_issue['number']
    print(f"Found DATA-1: Issue #{issue_num}")
    
    # Tick the boxes
    body = data1_issue['body']
    body = body.replace("- [ ] Identify and document data source", "- [x] Identify and document data source")
    body = body.replace("- [ ] Pull raw data into", "- [x] Pull raw data into")
    body = body.replace("- [ ] Record season coverage and row counts", "- [x] Record season coverage and row counts")
    
    # Update and close
    update_url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}"
    update_data = {
        "body": body,
        "state": "closed"
    }
    github_request(update_url, method="PATCH", data=update_data)
    print(f"Issue #{issue_num} successfully updated and closed.")

if __name__ == "__main__":
    main()
