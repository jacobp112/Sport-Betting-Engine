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
    
    # Close all issues starting with FEAT-1, FEAT-2, FEAT-3, FEAT-4, FEAT-5, FEAT-6
    for i in issues:
        title = i['title']
        number = i['number']
        if any(title.startswith(prefix + " ") for prefix in ["FEAT-1", "FEAT-2", "FEAT-3", "FEAT-4", "FEAT-5", "FEAT-6"]):
            print(f"Closing {title} (Issue #{number})...")
            update_url = f"https://api.github.com/repos/{REPO}/issues/{number}"
            # Tick the checkboxes in body if present
            body = i.get('body', '')
            if body:
                body = body.replace("- [ ] ", "- [x] ")
            update_data = {
                "body": body,
                "state": "closed"
            }
            github_request(update_url, method="PATCH", data=update_data)
            print(f"Closed Issue #{number}")

if __name__ == "__main__":
    main()
