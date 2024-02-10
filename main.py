from collections import UserDict
from datetime import date, datetime
import pickle
import os

# Directory and file for storing the address book data
STORAGE_DIR = os.getcwd()
STORAGE_FILE = os.path.join(STORAGE_DIR, 'address_book.pkl')

# Base class representing a field in a record
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

# Class representing a name, inheriting from Field
class Name(Field):
    ...

# Class representing a phone number, inheriting from Field
class Phone(Field):
    def __init__(self, value):
        self.value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return str(self.value)

    @value.setter
    def value(self, new_value: str):
        # Validation for phone number format
        if len(new_value) != 10:
            raise ValueError("Phone number should be 10 digits long.")
        if not new_value.isdigit():
            raise ValueError("Phone number should only include digits.")
        self._value = new_value

# Class representing a birthday, inheriting from Field
class Birthday(Field):
    def __init__(self, value):
        self._value = None
        self.birthday = value

    @property
    def birthday(self):
        return self._value

    @birthday.setter
    def birthday(self, new_value) -> datetime:
        # Validation for birthday format
        if new_value:
            try:
                self._value = date.fromisoformat(new_value)
            except ValueError:
                raise ValueError("Invalid birthday format. Use YYYY-MM-DD.")

# Custom exception for missing name
class MissingNameError(Exception):
    pass

# Custom exception for invalid birthday format
class InvalidBirthdayFormatError(Exception):
    pass

# Class representing a contact record
class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phone_numbers = []
        self.birthday = Birthday(birthday)

    def add_phone(self, phone):
        self.phone_numbers.append(Phone(phone))

    def remove_phone(self, phone_to_remove):
        self.phone_numbers = list(
            filter(lambda phone: phone.value != phone_to_remove, self.phone_numbers))

    def edit_phone(self, old_phone, new_phone):
        search_for_phone = list(
            filter(lambda phone: phone.value == old_phone, self.phone_numbers))
        if search_for_phone:
            search_for_phone[0].value = new_phone
        else:
            raise ValueError('Phone number not found')

    def find_phone(self, phone_to_find):
        search_for_phone = list(
            filter(lambda phone: phone.value == phone_to_find, self.phone_numbers))
        if search_for_phone:
            return search_for_phone[0]

    def days_to_birthday(self):
        if not self.birthday:
            return None

        birthdate = self.birthday.birthday
        today = date.today()
        next_birthday = birthdate.replace(year=today.year)

        if today > next_birthday:
            next_birthday = next_birthday.replace(year=today.year + 1)

        return (next_birthday - today).days

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        birthday_info = f", Birthday: {self.birthday.birthday}" if self.birthday.birthday else ""
        return f"Contact name: {self.name.value}, phones: {', '.join(str(phone) for phone in self.phone_numbers)}{birthday_info}"

# Class representing an address book, inheriting from UserDict
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name_value):
        return self.data.get(name_value)

    def delete(self, name):
        self.data.pop(name, None)

    def iterator(self, n):
        for i in range(0, len(self.data), n):
            yield list(self.data.values())[i:i + n]

    def save(self):
        # Save the address book to a file using pickle
        with open(STORAGE_FILE, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def from_storage(cls):
        # Load the address book from a file using pickle
        if not os.path.exists(STORAGE_FILE):
            return AddressBook()

        with open(STORAGE_FILE, 'rb') as f:
            return pickle.load(f)

# Create an instance of the address book
contacts = AddressBook.from_storage()

# Decorator to handle input errors
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Enter user name"
        except ValueError as ve:
            return str(ve)
        except MissingNameError:
            return "Name is missing. Please provide a name."
        except InvalidBirthdayFormatError:
            return "Invalid birthday format. Use YYYY-MM-DD."
        except Exception as e:
            return "Invalid command. Please try again."

    return wrapper

# Function to add a new contact to the address book
@input_error
def add_contact(command):
    parts = command.split(' ')
    name, phone = parts[1], parts[2]

    if not name:
        raise MissingNameError()

    birthday = None
    if len(parts) > 3:
        birthday = parts[3]

    if name in contacts.data.keys():
        return f'Contact with name {name} already exists.'

    new_record = Record(name, birthday)
    new_record.add_phone(phone)
    contacts.add_record(new_record)

    return f"Added {name} with phone number {phone}"

# Function to search for contacts in the address book
@input_error
def find_contacts(command):
    query = command.split(' ', 1)[1]
    query = query.strip()

    if not query:
        return 'Search query is too small'

    heap = list(map(lambda record: dict(name=str(record.name), heap=str(
        record.name) + " " + ";".join(map(str, record.phone_numbers))), contacts.data.values()))

    results = []

    for heap_item in heap:
        name = heap_item['name']
        if query.lower() in heap_item['heap'].lower():
            record = contacts.find(name)
            results.append(
                f"{name:20} Birthday: {record.birthday.birthday.isoformat() if record.birthday.birthday else '-' * 10}        {', '.join(str(phone) for phone in record.phone_numbers)}")

    return results if results else 'No contacts found that match your query'

# Function to change the phone number or birthday of a contact
@input_error
def change_contact(command):
    parts = command.split(' ', 3)
    name, phone = parts[1], parts[2]

    birthday = None
    if len(parts) > 3:
        birthday = parts[3]

    if name not in contacts.data.keys():
        return f'Contact with name {name} does not exist. Use "add" to create a new contact.'

    record = contacts.data[name]
    record.phone_numbers = [Phone(phone)]
    record.birthday.birthday = birthday

    return f"Changed phone number for {name} to {phone}"

# Function to get the phone number(s) of a contact
@input_error
def get_phone(command):
    name = command.split(' ', 1)[1]
    record = contacts.find(name)

    if record:
        return f"Phone number for {name}: {', '.join(str(phone) for phone in record.phone_numbers)}"
    else:
        return f"No contact found for {name}"

# Function to display all contacts in the address book
@input_error
def show_all():
    if contacts:
        return [f"{name:20} Birthday: {record.birthday.birthday.isoformat() if record.birthday.birthday else '-' * 10}        {', '.join(str(phone) for phone in record.phone_numbers)}" for name, record in contacts.data.items()]
    else:
        return "You have no contacts"

# Function to save changes and exit the program
def bye():
    contacts.save()
    print("Good bye!")

# Main program loop
def main():
    print("Welcome! How can I help you?")
    while True:
        user_input = input("> ")
        user_input_lower = user_input.lower()

        if user_input == "hello":
            print("How can I help you?")
        elif user_input_lower.startswith("add"):
            print(add_contact(user_input))
        elif user_input_lower.startswith("change"):
            print(change_contact(user_input))
        elif user_input_lower.startswith("phone"):
            print(get_phone(user_input))
        elif user_input_lower.startswith("find"):
            results = find_contacts(user_input)

            if isinstance(results, list):
                results.sort()
                print('\n'.join(results))
            else:
                print(results)
        elif user_input_lower == "show all":
            all_contacts = show_all()

            if isinstance(all_contacts, list):
                all_contacts.sort()
                print('\n'.join(all_contacts))
            else:
                print(all_contacts)
        elif user_input_lower in ["bye", "good bye", "close", "exit"]:
            bye()
            break
        elif not user_input_lower.strip():
            ...
        else:
            print("Invalid command. Please try again.")

# Entry point for the program
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit, EOFError):
        print('\n')
        bye()
