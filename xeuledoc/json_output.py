"""
This module is used to output xeuledoc results in JSON format.

Usage:
    python -m xeuledoc.json_output [GOOGLE_DOCUMENT_RESOURCE_URL] [-o OUTPUT_FILE]

Example:
    python -m xeuledoc.json_output https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
    python -m xeuledoc.json_output https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms --output output.json
"""
import argparse
import datetime
from html import parser
import json
import pathlib
import sys

import httpx


def main():
    parser = argparse.ArgumentParser(description="Output xeuledoc results in JSON format.")
    parser.add_argument("url", help="Google document resource URL. It basically begin with the string 'https://docs.google.com'.")
    parser.add_argument("-o", "--output", help="Output file.")
    args = parser.parse_args()
    doc_link = args.url
    output = args.output
    
    # Set Result Output Dict
    result_output = {
        "document_id": None,
        "document_link": doc_link,
        "created_date": None,
        "modified_date": None,
        "user_permissions": [],
        "public_permissions": [],
        "owner": None
    }
    
    # Get the document ID
    document_id = ''.join([x for x in doc_link.split("?")[0].split("/") if len(x) in (33, 44)])
    if not document_id:
        print("Document ID not found.\nPlease provide a valid Google document resource URL.", file=sys.stderr)
        sys.exit(1)
    result_output["document_id"] = document_id
    
    # Set headers
    headers = {"X-Origin": "https://drive.google.com"}
    client = httpx.Client(headers=headers)
    
    # Get the document information
    docinfo_url = f"https://clients6.google.com/drive/v2beta/files/{document_id}?fields=alternateLink%2CcopyRequiresWriterPermission%2CcreatedDate%2Cdescription%2CdriveId%2CfileSize%2CiconLink%2Cid%2Clabels(starred%2C%20trashed)%2ClastViewedByMeDate%2CmodifiedDate%2Cshared%2CteamDriveId%2CuserPermission(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cpermissions(id%2Cname%2CemailAddress%2Cdomain%2Crole%2CadditionalRoles%2CphotoLink%2Ctype%2CwithLink)%2Cparents(id)%2Ccapabilities(canMoveItemWithinDrive%2CcanMoveItemOutOfDrive%2CcanMoveItemOutOfTeamDrive%2CcanAddChildren%2CcanEdit%2CcanDownload%2CcanComment%2CcanMoveChildrenWithinDrive%2CcanRename%2CcanRemoveChildren%2CcanMoveItemIntoTeamDrive)%2Ckind&supportsTeamDrives=true&enforceSingleParent=true&key=AIzaSyC1eQ1xj69IdTMeii5r7brs3R90eck-m7k"

    retries = 100
    for retry in range(retries):
        req = client.get(docinfo_url)
        if "File not found" in req.text:
            print("This file does not exist or is not public.", file=sys.stderr)
            sys.exit(1)
        elif "rateLimitExceeded" in req.text:
            # print(f"Rate-limit detected, retrying... {retry+1}/{retries}", file=sys.stderr, end="\r")
            continue
        else:
            break
    else:
        print("Rate-limit exceeded. Try again later.", file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(req.text)
    
    # Extracting informations
    
    ## Dates
    created_date = datetime.datetime.strptime(data["createdDate"], '%Y-%m-%dT%H:%M:%S.%fz').isoformat()
    modified_date = datetime.datetime.strptime(data["modifiedDate"], '%Y-%m-%dT%H:%M:%S.%fz').isoformat()
    result_output["created_date"] = created_date
    result_output["modified_date"] = modified_date
    
    ## Permissions
    user_permissions = []
    if data["userPermission"]:
        if data["userPermission"]["id"] == "me":
            user_permissions.append(data["userPermission"]["role"])
            if "additionalRoles" in data["userPermission"]:
                user_permissions += data["userPermission"]["additionalRoles"]
    result_output["user_permissions"] = user_permissions
    
    public_permissions = []
    owner = None
    for permission in data["permissions"]:
        if permission["id"] in ["anyoneWithLink", "anyone"]:
            public_permissions.append(permission["role"])
            if "additionalRoles" in data["permissions"]:
                public_permissions += permission["additionalRoles"]
        elif permission["role"] == "owner":
            owner = permission
    result_output["public_permissions"] = public_permissions

    ## Owner
    if owner:
        result_output["owner"] = owner
    
    
    # Output the result
    if output:
        with open(output, "w") as f:
            json.dump(result_output, f, indent=4, ensure_ascii=False)
        print(f"{pathlib.Path(output).resolve()}")
    else:
        print(json.dumps(result_output, indent=4, ensure_ascii=False))
    

if __name__ == "__main__":
    main()
