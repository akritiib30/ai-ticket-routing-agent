import csv
import random

random.seed(42)

categories = {
    "Infrastructure": {
        "issues": [
            "the internal server is unavailable",
            "the company server is not responding",
            "an internal service has stopped working",
            "the server connection keeps timing out",
            "the infrastructure service is extremely slow",
            "the internal system cannot be reached",
            "the server became unavailable during work",
            "the company-hosted service is not responding",
            "the internal server keeps disconnecting",
            "a business server is currently offline",
        ],
        "resolutions": [
            "Check server health and review the infrastructure logs.",
            "Verify server availability and restart the affected service if required.",
            "Check the infrastructure service and escalate to the infrastructure team if necessary.",
        ],
    },

    "Application": {
        "issues": [
            "the business application keeps crashing",
            "the application will not open",
            "the software freezes whenever I use it",
            "the application displays an unexpected error",
            "the company application suddenly stopped working",
            "the application becomes unresponsive",
            "the application closes immediately after opening",
            "one of our business applications is behaving incorrectly",
            "the application is extremely slow",
            "I cannot complete my work because the application keeps failing",
        ],
        "resolutions": [
            "Restart the application and check whether the problem continues.",
            "Check the application logs and install the latest available update.",
            "Verify the application configuration and escalate to application support if required.",
        ],
    },

    "Security": {
        "issues": [
            "I noticed a suspicious login on my account",
            "I received an email that looks like a phishing attempt",
            "I think my account may have been compromised",
            "my computer may have malware",
            "there is unusual activity on my account",
            "I accidentally clicked a suspicious link",
            "I received a suspicious attachment",
            "someone may have accessed my account without permission",
            "my device is showing signs of malicious activity",
            "I am concerned about unauthorized activity",
        ],
        "resolutions": [
            "Secure the account, change the password, and contact Security Operations.",
            "Report the suspicious activity to the security team immediately.",
            "Disconnect the affected device from the network and contact Security Operations.",
        ],
    },

    "Database": {
        "issues": [
            "the database connection is failing",
            "database queries are taking too long",
            "I cannot access the company database",
            "the database server is not responding",
            "records are not loading from the database",
            "database requests keep timing out",
            "the database connection drops unexpectedly",
            "our application cannot retrieve database records",
            "database performance has suddenly become very slow",
            "I am unable to retrieve information from the database",
        ],
        "resolutions": [
            "Check database connectivity and review the database server logs.",
            "Verify database availability and investigate slow-running queries.",
            "Check database permissions and escalate to database support if required.",
        ],
    },

    "Storage": {
        "issues": [
            "the shared storage is almost full",
            "I cannot save files to the shared drive",
            "the disk is running out of space",
            "storage capacity has been exhausted",
            "files cannot be uploaded to the storage system",
            "the shared drive is unavailable",
            "our storage space is nearly full",
            "I am unable to access files on the shared drive",
            "the system reports insufficient disk space",
            "new files cannot be saved because storage is full",
        ],
        "resolutions": [
            "Check available storage and remove unnecessary files if appropriate.",
            "Verify storage connectivity and available disk capacity.",
            "Check storage permissions and escalate to storage support if needed.",
        ],
    },

    "Network": {
        "issues": [
            "the company VPN is not connecting",
            "the office internet connection is very slow",
            "Wi-Fi keeps disconnecting",
            "the network connection keeps failing",
            "I cannot access the company network",
            "the VPN connection keeps dropping",
            "I am unable to connect to internal network resources",
            "my network connection becomes unstable during work",
            "the corporate network is unreachable",
            "remote access to the company network is not working",
        ],
        "resolutions": [
            "Restart the VPN client and verify the network connection.",
            "Check network connectivity and restart the network adapter.",
            "Verify VPN settings and escalate to network support if required.",
        ],
    },

    "Access Management": {
        "issues": [
            "I forgot my password",
            "my account is locked",
            "I cannot log into my company account",
            "I need access to an internal system",
            "my login credentials are not working",
            "I need my account access restored",
            "I am unable to sign in with my company credentials",
            "my account has been locked after several login attempts",
            "I need permission to access a company application",
            "my existing account does not have the required access",
        ],
        "resolutions": [
            "Reset the password and verify account access.",
            "Unlock the account and confirm the user's permissions.",
            "Verify access permissions and escalate to access management if required.",
        ],
    },
}


sentence_templates = [
    "I am having trouble because {issue}.",
    "Please help me. {issue}.",
    "I need assistance with this problem: {issue}.",
    "This started happening today: {issue}.",
    "I am unable to continue my work because {issue}.",
    "Can someone help me resolve this? {issue}.",
    "I have been trying to fix this, but {issue}.",
    "Our team is facing the following issue: {issue}.",
    "This issue is preventing me from working: {issue}.",
    "I would like to report a problem where {issue}.",
    "Something appears to be wrong because {issue}.",
    "I need technical support because {issue}.",
]

title_templates = [
    "{issue}",
    "Unable to resolve: {issue}",
    "Support required: {issue}",
    "Problem with {issue}",
    "Issue reported: {issue}",
]

priority_weights = {
    "Low": 0.25,
    "Medium": 0.50,
    "High": 0.25,
}


def choose_priority():
    return random.choices(
        list(priority_weights.keys()),
        weights=list(priority_weights.values()),
        k=1
    )[0]


rows = []

# Generate approximately equal numbers for every category
base_count = 142
extra_categories = ["Infrastructure", "Application", "Database", "Storage"]

for category, data in categories.items():

    count = base_count

    if category in extra_categories:
        count += 1

    for _ in range(count):

        issue = random.choice(data["issues"])
        sentence = random.choice(sentence_templates)
        title_template = random.choice(title_templates)

        description = sentence.format(issue=issue)
        title = title_template.format(issue=issue).capitalize()
        resolution = random.choice(data["resolutions"])
        priority = choose_priority()

        rows.append({
            "title": title,
            "description": description,
            "category": category,
            "resolution": resolution,
            "priority": priority,
        })


# Shuffle the dataset
random.shuffle(rows)

# Remove exact duplicates
unique_rows = []
seen = set()

for row in rows:
    row_key = (
        row["title"],
        row["description"],
        row["category"],
        row["resolution"],
        row["priority"],
    )

    if row_key not in seen:
        seen.add(row_key)
        unique_rows.append(row)


# If duplicates reduced the dataset, create additional variations
while len(unique_rows) < 1000:

    category = random.choice(list(categories.keys()))
    data = categories[category]

    issue = random.choice(data["issues"])
    sentence = random.choice(sentence_templates)
    title_template = random.choice(title_templates)

    description = sentence.format(issue=issue)

    # Add a small variation to guarantee uniqueness
    variation = random.randint(1, 100000)

    title = (
        title_template.format(issue=issue).capitalize()
        + f" #{variation}"
    )

    resolution = random.choice(data["resolutions"])
    priority = choose_priority()

    row = {
        "title": title,
        "description": description,
        "category": category,
        "resolution": resolution,
        "priority": priority,
    }

    row_key = tuple(row.values())

    if row_key not in seen:
        seen.add(row_key)
        unique_rows.append(row)


# Keep exactly 1000 tickets
rows = unique_rows[:1000]

output_file = "tickets.csv"

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "title",
            "description",
            "category",
            "resolution",
            "priority",
        ],
    )

    writer.writeheader()
    writer.writerows(rows)


print("======================================")
print("DATASET CREATED SUCCESSFULLY")
print("======================================")

print(f"Total tickets: {len(rows)}")

print("\nCategory distribution:")

counts = {}

for row in rows:
    category = row["category"]
    counts[category] = counts.get(category, 0) + 1

for category, count in sorted(counts.items()):
    print(f"{category}: {count}")

print("\nDuplicate rows:", len(rows) - len(set(
    (
        r["title"],
        r["description"],
        r["category"],
        r["resolution"],
        r["priority"]
    )
    for r in rows
)))

print("\nDataset saved as:", output_file)