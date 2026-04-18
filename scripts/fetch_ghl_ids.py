"""
Run once to fetch pipeline stage IDs, custom field IDs, and workflow IDs from GHL.
Usage: python scripts/fetch_ghl_ids.py
Copy the output into your .env file.
"""
import os
import sys
import httpx

PIT_TOKEN = os.getenv("GHL_PIT_TOKEN", "pit-434e3525-02b4-4960-a9e2-fc3f58d4d0fb")
LOCATION_ID = os.getenv("GHL_LOCATION_ID", "AWQqYSyxdYeqqhoLc0ef")
BASE = "https://services.leadconnectorhq.com"
HEADERS = {
    "Authorization": f"Bearer {PIT_TOKEN}",
    "Version": "2021-07-28",
    "Content-Type": "application/json",
}


def get(path, params=None):
    resp = httpx.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def main():
    print("\n=== PIPELINES & STAGES ===\n")
    try:
        data = get("/opportunities/pipelines", params={"locationId": LOCATION_ID})
        for pipeline in data.get("pipelines", []):
            print(f"Pipeline: {pipeline['name']} | ID: {pipeline['id']}")
            print(f"  GHL_PIPELINE_ID={pipeline['id']}")
            for stage in pipeline.get("stages", []):
                print(f"  Stage: {stage['name']} | ID: {stage['id']}")
    except Exception as e:
        print(f"  ERROR fetching pipelines: {e}")

    print("\n=== CUSTOM FIELDS ===\n")
    try:
        data = get(f"/locations/{LOCATION_ID}/customFields")
        for field in data.get("customFields", []):
            print(f"Field: {field.get('name', 'N/A')} | ID: {field['id']}")
    except Exception as e:
        print(f"  ERROR fetching custom fields: {e}")

    print("\n=== WORKFLOWS ===\n")
    try:
        data = get(f"/workflows/", params={"locationId": LOCATION_ID})
        for wf in data.get("workflows", []):
            print(f"Workflow: {wf.get('name', 'N/A')} | ID: {wf['id']}")
    except Exception as e:
        print(f"  Could not fetch workflows: {e}")

    print("\n=== .ENV MAPPING GUIDE ===\n")
    print("After running this script, copy the IDs above to your .env file:")
    print()
    print("# Pipeline stages — create these in GHL first if they don't exist:")
    print("# New Lead, Hot Lead, Mid Lead, Cold Lead, In Conversation,")
    print("# Call Scheduled, Enrolled, Not Interested")
    print()
    print("GHL_PIPELINE_ID=<pipeline_id from above>")
    print("GHL_STAGE_NEW_LEAD=<stage_id for 'New Lead'>")
    print("GHL_STAGE_HOT=<stage_id for 'Hot Lead'>")
    print("GHL_STAGE_MID=<stage_id for 'Mid Lead'>")
    print("GHL_STAGE_COLD=<stage_id for 'Cold Lead'>")
    print("GHL_STAGE_IN_CONVERSATION=<stage_id for 'In Conversation'>")
    print("GHL_STAGE_CALL_SCHEDULED=<stage_id for 'Call Scheduled'>")
    print("GHL_STAGE_ENROLLED=<stage_id for 'Enrolled'>")
    print("GHL_STAGE_NOT_INTERESTED=<stage_id for 'Not Interested'>")
    print()
    print("# Custom fields — match by field name:")
    print("GHL_FIELD_EXPERIENCE=<field_id for 'Have you worked with epoxy/flooring?'>")
    print("GHL_FIELD_GOAL=<field_id for 'What is your main goal?'>")
    print("GHL_FIELD_INVESTMENT=<field_id for 'How soon are you ready to invest?'>")
    print()
    print("# Workflows — create these in GHL Automations:")
    print("GHL_WORKFLOW_NURTURE_ROI=<workflow_id for ROI nurture>")
    print("GHL_WORKFLOW_NURTURE_CLASS_INFO=<workflow_id for class info nurture>")
    print("GHL_WORKFLOW_FOLLOWUP_HOT=<workflow_id for hot lead follow-up>")
    print("GHL_WORKFLOW_FOLLOWUP_MID=<workflow_id for mid lead follow-up>")
    print("GHL_WORKFLOW_FOLLOWUP_COLD=<workflow_id for cold lead follow-up>")
    print()


if __name__ == "__main__":
    main()
