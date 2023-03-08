# python-aws

Getting Started

1. Home Page
The Home page informs the user about Tele-A-Doctor and has two separate login options for doctors and patients.


2. Doctor Home Page
This page displays options for the Doctor. The Doctor can update account details, manage appointments and view patient records.

2.1 My Account
This shows the doctor’s email id and location, which can be updated. It also has a tab: ‘Add available slots’, which allows the doctor to add slots for each day of the week. It alsoallows the doctor to change password and delete account.


2.2 Manage Appointments
This shows the appointments requested by the patients. The doctor can choose to approve or reject the appointment. If the appointment is completed, the doctor can mark it as complete. If the patient did not make it to the appointment, the doctor can mark it as failed (this sends an email to the patient). The doctor can also message the patient.


2.3 View Patient Records
This allows the doctor to view the patient’s details (email, phone, age, postal code and issues). The doctor can also upload prescriptions and download past prescriptions.

3. Patient Home Page
This page displays options for the Patient. The Patient can update account details, find doctors, view appointments and view prescriptions.

3.1 My Account
This shows the patient’s email id and location, which can be updated. It also has a tab: ‘Add health issue’, which allows the patient to add their health issues.


3.2 Find Doctors
The patient can see available doctors in a specified radius. The patient can select the radius from the drop down (5, 10, 15, 20 25 kilometres), and select the slot to confirm the appointment.

3.3 View Appointments
This allows the patient to view, cancel and reschedule an appointment. It also allows the patient to message the doctor.

3.4 View Prescriptions
This allows the patient to download the prescription uploaded by the doctor.


4. Messaging
Doctors and patients are allowed to message each other based on the appointment status. Once the appointment status is completed or failed, neither the doctor nor the patient is allowed to message each other. This is to allow the patients to schedule a new appointment if they want to notify the doctor of their health issues. The messages are stored in S3 and retrieved when required.