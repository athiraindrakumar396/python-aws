import boto3
from app.config import db_config, app_config, s3_config

AWS_ACCESS_KEY_ID = s3_config["AWS_ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = s3_config["AWS_SECRET_KEY"]
REGION_NAME = s3_config["REGION_NAME"]

client = boto3.client(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
)
resource = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
)

PatientsTable = resource.Table('Patients')
DoctorsTable = resource.Table('Doctors')
SlotsTable = resource.Table('Slots')
SelectedSlots = resource.Table('SelectedSlots')
MedicalHistory = resource.Table('MedicalHistory')

def createTablePatients():
    client.create_table(
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'name',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],
        TableName='Patients',  # Name of the table
        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'name',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

def createTableDoctors():
    client.create_table(
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'name',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],
        TableName='Doctors',  # Name of the table
        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'name',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

def createTableDoctorSlots():
    client.create_table(
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'name',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],
        TableName='Slots',  # Name of the table
        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'name',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

def createTablePatientSlots():
    client.create_table(
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'patient_name',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],
        TableName='SelectedSlots',  # Name of the table
        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'patient_name',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

def createTableMedicalHistory():
    client.create_table(
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'date',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],
        TableName='MedicalHistory',  # Name of the table
        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'date',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )


def addPersonToPatients(name, password, zip, state, age, phone, is_patient=1, doctor=None):
    response = PatientsTable.put_item(
        Item={
            'name': name,
            'password': password,
            'zip': zip,
            'state': state,
            'is_patient': is_patient,
            'doctor': doctor,
            'age' : age,
            'phone' : phone
        }
    )
    return response

def addPersonToDoctors(name, password, zip, state, is_doctor=1):
    response = DoctorsTable.put_item(
        Item={
            'name': name,
            'password': password,
            'zip': zip,
            'state': state,
            'is_doctor': is_doctor,
        }
    )
    return response

def addSlotToSlots(name, day, start_time, end_time):
    response = SlotsTable.put_item(
        Item={
            'name': name,
            'day': day,
            'start_time': start_time,
            'end_time': end_time
        }
    )
    return response

def addPatientSlotToSlots(patient_name, doctor_name, day, slot, status):
    response = SelectedSlots.put_item(
        Item={
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'day': day,
            'slot': slot,
            'status': status
        }
    )
    return response

def addPatientToMedicalHistory(date, patient_name, issue):
    response = MedicalHistory.put_item(
        Item={
            'date' : date,
            'patient_name': patient_name,
            'issue': issue
        }
    )
    return response


def GetPersonFromPatientsUsingName(name):
    response = PatientsTable.get_item(
        Key={
            'name': name
        },
        AttributesToGet=[
            'name', 'password', 'is_patient', 'zip', 'state', 'doctor', 'phone', 'age'
        ]
    )
    return response

def GetPersonFromDoctorsUsingName(name):
    response = DoctorsTable.get_item(
        Key={
            'name': name
        },
        AttributesToGet=[
            'name', 'password', 'is_doctor', 'zip', 'state'
        ]
    )
    return response

def GetSlotFromSlotsUsingName(name):
    response = SlotsTable.get_item(
        Key={
            'name': name
        },
        AttributesToGet=[
            'day', 'start_time', 'end_time'
        ]
    )
    return response

def GetPatientSlotFromSlotsUsingName(patient_name):
    response = SelectedSlots.get_item(
        Key={
            'patient_name': patient_name
        },
        AttributesToGet=[
            'doctor_name', 'day', 'slot', 'status'
        ]
    )
    return response

def UpdatePasswordInPatient(name, password):
    response = PatientsTable.update_item(
        Key={
            'name': name
        },
        AttributeUpdates={
            'password': {
                'Value': password,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def UpdateDoctorInPatient(name, email):
    response = PatientsTable.update_item(
        Key={
            'name': name
        },
        AttributeUpdates={
            'doctor': {
                'Value': email,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def UpdatePasswordInDoctor(name, password):
    response = DoctorsTable.update_item(
        Key={
            'name': name
        },
        AttributeUpdates={
            'password': {
                'Value': password,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def UpdateSlotInDoctor(name, doctor_name, day, slot, status):
    response = SelectedSlots.update_item(
        Key={
            'patient_name': name
        },
        AttributeUpdates={
            'doctor_name' : {
                'Value': doctor_name,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'day': {
                'Value': day,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'slot': {
                'Value': slot,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'status': {
                'Value': status,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def UpdateStatusSlotInDoctor(name, status):
    response = SelectedSlots.update_item(
        Key={
            'patient_name': name
        },
        AttributeUpdates={
            'status': {
                'Value': status,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def DeleteAnItemFromSlot(name):
    response = SlotsTable.delete_item(
        Key = {
            'name': name
        }
    )
    return response

def DeleteAnItemFromPatient(name):
    response = PatientsTable.delete_item(
        Key = {
            'name': name
        }
    )
    return response

def DeleteAnItemFromDoctor(name):
    response = DoctorsTable.delete_item(
        Key = {
            'name': name
        }
    )
    return response

def DeleteAnItemFromPatientsSlots(name):
    response = SelectedSlots.delete_item(
        Key = {
            'patient_name': name
        }
    )
    return response

def UpdateDoctor(name, zip, state):
    response = DoctorsTable.update_item(
        Key={
            'name': name
        },
        AttributeUpdates={
            'zip': {
                'Value': zip,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'state': {
                'Value': state,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def UpdatePatient(name, zip, state, age, phone):
    response = PatientsTable.update_item(
        Key={
            'name': name
        },
        AttributeUpdates={
            'zip': {
                'Value': zip,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'state': {
                'Value': state,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'age': {
                'Value': age,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'phone': {
                'Value': phone,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response

def uploadPrescription(date, prescription, doctor):
    response = MedicalHistory.update_item(
        Key={
            'date': date
        },
        AttributeUpdates={
            'prescription': {
                'Value': prescription,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            },
            'doctor': {
                'Value': doctor,
                'Action': 'PUT'  # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues="UPDATED_NEW"  # returns the new updated values
    )
    return response
