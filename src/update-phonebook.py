#!/usr/bin/env python3

#
# Generates a phone book compatible with Grandstream DP750 from
# a directory containing vCard files.
#
# Uses:
#  - vdirsyncer - to sync contacts from another source
#  - vobject - to read vCard files
#

import sys
import os
import pathlib
import subprocess
import re
import vobject
import xml.etree.ElementTree as ET

def IsCompany(card):
    if not 'org' in card.contents:
        return False

    if 'X-ABShowAs' in card.contents:
        return next(card.contents['X-ABShowAs']).value.lower() == 'company'
    else:
        name = card.n.value
        return (not name.given and
                not name.family)

MIN_NUMBER_LENGTH = 10
PHONE_TYPES = {
    'HOME': lambda c:'Home',
    'WORK': lambda c:'Work',
    'CELL': lambda c:'Mobile',
    'MAIN': lambda c:'Work' if IsCompany(c) else 'Home'
}

def ValidPhoneNumber(number):
    return re.match(r'^[\d\(\)\-+\s]+$', number)

def CleanPhoneNumber(number):
    return re.sub(r'\D', '', number)

def FindPhoneNumbers(card):
    result = {}

    if 'tel' in item.contents:
        numbers = [(t.value, [x.upper() for x in t.params['TYPE']]) for t in item.contents['tel'] if 'TYPE' in t.params]
        numbers = [(n, t) for (n, t) in numbers if ValidPhoneNumber(n) and 'VOICE' in t or 'MAIN' in t]

        for (num, types) in numbers:
            num = CleanPhoneNumber(num)
            if len(num) >= MIN_NUMBER_LENGTH:
                result_type = next((PHONE_TYPES[t](card) for t in types if t in PHONE_TYPES), None)
                if result_type and not result_type in result:
                    result[result_type] = num
    
    return result;
                
def SubElementWithText(parent, tag, text):
    element = ET.SubElement(parent, tag)
    element.text = text
    return element

def PrettyPrint(current, parent=None, index=-1, depth=0):
    for i, node in enumerate(current):
        PrettyPrint(node, current, i, depth + 1)
    if parent is not None:
        if index == 0:
            parent.text = '\n' + ('\t' * depth)
        else:
            parent[index - 1].tail = '\n' + ('\t' * depth)
        if index == len(parent) - 1:
            current.tail = '\n' + ('\t' * (depth - 1))

if len(sys.argv) < 3:
    print('Usage: update-phonebook [vcard path] [phonebook file] {sync arguments}')
    exit(1)

input_path = pathlib.Path(sys.argv[1])
output_path = pathlib.Path(sys.argv[2])

output_base_path = output_path.with_name(re.sub(r'^(.*)(\.[^.]*)$', r'\1.base\2', output_path.name))

input_files_before = [entry for entry in input_path.glob('*.vcf') if entry.is_file()]

#
# Run the contact sync tool
#
print('Sync contacts')
try:
    sync_cmd = ['vdirsyncer', 'sync'] + sys.argv[3:]
    print(f' - Executing: {" ".join(sync_cmd)}')
    subprocess.run(sync_cmd)
except:
    print(f' - Failed to run sync command: {sys.exc_info()[1]}')
finally:
    input_files_after = [entry for entry in input_path.glob('*.vcf') if entry.is_file()]

#
# Check if we need to (re-)generate the phone book
#
print('Determine if phone book needs to be updated')
output_exists = output_path.exists();
output_mtime = output_path.stat().st_mtime_ns if output_exists else 0

# check if output exists
print(f' - Output file {output_path} exists?: {output_exists}')
generate = not output_exists

if not generate:
    # check if base file has been updated?
    if output_base_path.exists():
        base_file_updated = output_base_path.stat().st_mtime_ns > output_mtime
        print (f' - Base file {output_base_path} updated? {base_file_updated}')
        generate |= base_file_updated

    # check if any existing files have been removed
    removed_file_count = len([file for file in input_files_before if not file.exists()])
    print(f' - Contact files removed?: {removed_file_count}')
    generate |= removed_file_count > 0

    # check if any contact files are new or updated
    updated_count = len([file for file in input_files_after 
                         if file.stat().st_mtime_ns > output_mtime or
                            not file in input_files_before])
    print(f' - New or updated contact files: {updated_count}')
    generate |= updated_count > 0

if not generate:
    print("Phone book is up to date, exiting")
    exit(0)

#
# Load all contact cards
#
print('Loading contact files')

cards = []
for file in input_files_after:
    with file.open('r') as file_stream:
        try:
            cards.append(vobject.readOne(file_stream))
        except:
            print(f' - Error reading {file}')
            raise

print(f' - {len(cards)} contacts found')

#
# Generate phone book
#
print('Generating phone book')

# load base phone book
book = None
if output_base_path.exists():
    try:
        print(f' - Loading base phone book: {output_base_path}')
        base = ET.parse(output_base_path)
        book = base.getroot()
    except:
        print(f'   Ignoring base phone book due to error: {sys.exc_info()[1]}')

if book is None:
    book = ET.Element("AddressBook")

# Generate contact details
print(' - Generating contacts:')
contact_count = 0
for item in cards:
    numbers = FindPhoneNumbers(item)
    if any(numbers):
        contact = ET.SubElement(book, 'Contact')

        # Choose fields to display for tha nem
        if IsCompany(item):
            first_name = None
            last_name = item.org.value[0]
        else:
            first_name = f'{item.n.value.prefix.strip()} {item.n.value.given.strip()}'.strip()
            last_name = item.n.value.family

        # If we only have a first name, put it in the last name
        # field so that it sorts better on the handsets.
        if first_name and not last_name:
            last_name = first_name
            first_name = None

        if first_name or last_name:
            contact_count += 1
            log_name = f'{first_name or ""} {last_name or ""}'.strip()

            if first_name:
                SubElementWithText(contact, 'FirstName', first_name)
            if last_name:
                SubElementWithText(contact, 'LastName', last_name)

            for t,n in numbers.items():
                phone = ET.SubElement(contact, 'Phone', {'type': t})
                phone_number = SubElementWithText(phone, 'phonenumber', n)           

print(f' - Total: {contact_count} contacts')

print(f'Writing output file: {output_path}')
PrettyPrint(book)
with output_path.open('wb') as output:
    ET.ElementTree(book).write(output, encoding='utf-8', xml_declaration=True)
