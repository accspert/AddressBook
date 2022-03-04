import re
import quopri

class Contact(object):
    """
    Contains the contact infromation,
    including a list of phone numbers.

    Arguments:
        object {[type]} -- [description]
    """

    def __init__(self):
        self.FirstName = ""
        self.LastName = ""
        self.Phonenumbers = []
        self.Email = []
        self.Address =""
        self.Birthday=""


def extract_number(line):
    """
    Extracts the phone number from a vCard-file line,
    by removing everything but numbers and '+'

    Arguments:
        line {string} -- the line to extract the phone number from

    Returns:
        string -- the phone number
    """

    line = line[line.index(":")+1:].rstrip()
    line = re.sub('[^0-9+]', '', line)
    return line


def generate_vcard_contact_string(contact):
    """
    Generates the vCard string for this contact.
    Will generate a sperate vCard for each phone number of the contact.

    Arguments:
        contact {Contact} -- the contact to generate the vCard string from

    Returns:
        string -- the generated vCard string
    """

    base = f"BEGIN:VCARD\n"
    base += f"N:{contact.LastName};{contact.FirstName}\n"
    for number in contact.Phonenumbers:
        base += f"TEL:{number}\n" 
    for email in contact.Email:
        base += f"EMAIL:{email}\n"
    base += f"ADR:{contact.Address}\n"
    base += f"BDAY:{contact.Birthday}\n"
    base += f"END:VCARD\n"
    return base

def import_contacts(file_name):

    contacts = []

    with open(file_name) as f:
        # current_contact = Contact()
        for line in f:
            # Some lines are build like "item1.TEL;...",
            # remove "item1.", "item2.", to ease parsing
            if line.startswith("item"):
                line = line[line.index(".")+1:]
    
            if "BEGIN:VCARD" in line:
                # Marks the start of a vCard,
                # create a blank contact to work with
                current_contact = Contact()
    
            elif line.startswith("N:"):
                # Line contains a name in the format N:LastName;FirstName;...;...;
                # Only LastName and FirstName will be used
                line = line.replace("N:", "")  # remove "N:" from line
                chunks = line.split(';')
                current_contact.LastName = chunks[0].strip()
                current_contact.FirstName = chunks[1].strip()
    
            elif line.startswith("TEL"):
                number = extract_number(line)
                if line:
                    current_contact.Phonenumbers.append(number)
                
            elif line.startswith("EMAIL"):
                match = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', line)
                if match:
                    current_contact.Email.append(match[0])
                
            elif line.startswith("ADR"):
                if not line.find('PRINTABLE:') !=-1:
                    if not current_contact.Address:
                        line = line.replace(";", " ")
                        line = line.replace("ADR", " ")
                        line = line.replace("HOME:", " ")
                        line = line.replace("WORK:", " ")
                        current_contact.Address = line.strip()
            elif line.startswith("BDAY"):
                if not current_contact.Birthday:
                    line = line.replace("BDAY:", "")
                    # line = line.replace(";", "")
    
                    current_contact.Birthday = line
    
            elif "END:VCARD" in line:
                # Marks the end of a vCard,
                # append contact to list
                contacts.append(current_contact)
    
    return contacts

def create_vcards(contacts):
    result =''
    for contact in contacts:
        # Generate a string containing a vCard for each of the contacts phone
        # numbers, append those string to create one big text containing everything
        result += generate_vcard_contact_string(contact)
    return result
