import os
import re
import urllib.request
import json
import ssl

# Disable SSL verification issues if any (optional, but good for local reliability on some setups)
ssl_context = ssl._create_unverified_context()

TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "jacobp112/Sport-Betting-Engine"
ROADMAP_PATH = "sports-betting-model-roadmap.md"

if not TOKEN:
    print("WARNING: GITHUB_TOKEN environment variable not set. Running in DRY-RUN mode.")
    DRY_RUN = True
else:
    print("GITHUB_TOKEN found. Running in LIVE mode.")
    DRY_RUN = False

def github_request(url, method="GET", data=None):
    if DRY_RUN:
        return None
    
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Sports-Betting-Engine-Setup-Script"
    }
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, headers=headers, method=method, data=req_data)
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            res_data = response.read()
            if res_data:
                return json.loads(res_data.decode("utf-8"))
            return {}
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise e
    except Exception as e:
        print(f"Network Error: {e}")
        raise e

def get_existing_milestones():
    if DRY_RUN:
        return {}
    print("Fetching existing milestones...")
    url = f"https://api.github.com/repos/{REPO}/milestones?state=all"
    milestones = github_request(url)
    return {m["title"]: m["number"] for m in milestones}

def create_milestone(title, description=""):
    print(f"Creating milestone: {title}")
    if DRY_RUN:
        return 999
    url = f"https://api.github.com/repos/{REPO}/milestones"
    data = {
        "title": title,
        "description": description,
        "state": "open"
    }
    res = github_request(url, method="POST", data=data)
    return res["number"]

def get_existing_issues():
    if DRY_RUN:
        return set()
    print("Fetching existing issues...")
    issues_set = set()
    page = 1
    while True:
        url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}"
        issues = github_request(url)
        if not issues:
            break
        for issue in issues:
            # Issues API also returns pull requests, check if it's a real issue
            if "pull_request" not in issue:
                issues_set.add(issue["title"])
        page += 1
    return issues_set

def create_issue(title, body, milestone_number, labels):
    print(f"Creating issue: {title}")
    if DRY_RUN:
        return
    url = f"https://api.github.com/repos/{REPO}/issues"
    data = {
        "title": title,
        "body": body,
        "milestone": milestone_number,
        "labels": labels
    }
    github_request(url, method="POST", data=data)

def parse_roadmap():
    if not os.path.exists(ROADMAP_PATH):
        raise FileNotFoundError(f"Roadmap file not found at {ROADMAP_PATH}")
        
    with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    epics = []
    current_epic = None
    current_story = None
    
    # Simple regexes
    epic_regex = re.compile(r'^##\s+(Epic\s+\d+:\s+.*)$')
    story_regex = re.compile(r'^\*\*`([^`]+)`\*\*\s*—\s*(.*)$')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for Epic
        epic_match = epic_regex.match(line)
        if epic_match:
            epic_title = epic_match.group(1)
            # Find Goal
            goal = ""
            # Look ahead for goal
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip().startswith("**Goal:**"):
                    goal = lines[j].strip().replace("**Goal:**", "").strip()
                    break
            current_epic = {
                "title": epic_title,
                "goal": goal,
                "stories": []
            }
            epics.append(current_epic)
            current_story = None
            i += 1
            continue
            
        # Check for Story
        story_match = story_regex.match(line)
        if story_match and current_epic is not None:
            story_id = story_match.group(1)
            story_desc = story_match.group(2)
            current_story = {
                "id": story_id,
                "description": story_desc,
                "body_lines": [],
                "labels": ["story"]
            }
            # Infer labels from story ID prefix
            prefix = story_id.split("-")[0].lower()
            if prefix == "setup":
                current_story["labels"].append("setup")
            elif prefix == "data":
                current_story["labels"].append("data")
            elif prefix == "feat":
                current_story["labels"].append("feature")
            elif prefix in ["model", "modeler"]:
                current_story["labels"].append("model")
            elif prefix == "bt":
                current_story["labels"].append("backtest")
            elif prefix == "valid":
                current_story["labels"].append("validation")
            elif prefix == "paper":
                current_story["labels"].append("paper-trading")
            elif prefix == "live":
                current_story["labels"].append("live")
            elif prefix == "risk":
                current_story["labels"].append("risk")
            elif prefix == "exec":
                current_story["labels"].append("infra")
            elif prefix == "mon":
                current_story["labels"].append("monitoring")
                
            current_epic["stories"].append(current_story)
            i += 1
            continue
            
        # If we are in a story, collect its lines
        if current_story and line and not line.startswith("##") and not line.startswith("---"):
            current_story["body_lines"].append(lines[i].rstrip())
            
        i += 1
        
    return epics

def main():
    print("Parsing roadmap...")
    epics = parse_roadmap()
    print(f"Found {len(epics)} Epics.")
    for ep in epics:
        print(f"  {ep['title']} ({len(ep['stories'])} stories)")
        
    # Get existing milestones and issues
    existing_milestones = get_existing_milestones()
    existing_issues = get_existing_issues()
    
    # Process Epics and Stories
    for epic in epics:
        epic_title = epic["title"]
        epic_goal = epic["goal"]
        
        # Get or create milestone
        if epic_title in existing_milestones:
            milestone_num = existing_milestones[epic_title]
            print(f"Milestone '{epic_title}' already exists (number {milestone_num}).")
        else:
            milestone_num = create_milestone(epic_title, description=epic_goal)
            
        # Create stories for this epic
        for story in epic["stories"]:
            story_title = f"{story['id']} — {story['description']}"
            
            # Check if issue already exists
            already_exists = False
            for existing in existing_issues:
                if existing.startswith(story["id"] + " —") or existing == story_title:
                    already_exists = True
                    break
            
            if already_exists:
                print(f"Issue '{story_title}' already exists. Skipping.")
                continue
                
            # Clean body
            body_text = "\n".join(story["body_lines"]).strip()
            # Standard issue body prefix
            body = f"### Goal\n{story['description']}\n\n{body_text}"
            
            create_issue(story_title, body, milestone_num, story["labels"])

if __name__ == "__main__":
    main()
