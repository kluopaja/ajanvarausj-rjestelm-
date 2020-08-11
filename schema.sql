CREATE TABLE Users
(
    id SERIAL PRIMARY KEY,
    username TEXT,
    password_hash TEXT
);
CREATE TABLE Polls
(
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES Users (id) ON DELETE CASCADE, --Also there was ON UPDATE CASCADE, check these!
    poll_name TEXT,
    poll_description TEXT,
    first_appointment_date date,
    last_appointment_date date,
    poll_end_time timestamp, --change name?
    has_final_results boolean,
    CHECK(first_appointment_date <= last_appointment_date)
);
CREATE TABLE PollMembers
(
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES Polls (id) ON DELETE CASCADE
);
CREATE TABLE MemberTimeGrades
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    --half open intervals [time_beginning, time_end)
    time_beginning timestamp,
    time_end timestamp,
    grade INTEGER, CHECK(time_beginning < time_end)
);
CREATE TABLE Customers
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    reservation_length interval
);
CREATE TABLE Resources
(
    resource_name TEXT UNIQUE,
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE 
);
CREATE TABLE UsersPollMembers
(
    user_id INTEGER REFERENCES Users (id) ON DELETE CASCADE,
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE
);
CREATE TABLE NewCustomerLinks
(
    poll_id INTEGER REFERENCES Polls (id) ON DELETE CASCADE,
    url_id TEXT,
    reservation_length interval
);
CREATE TABLE ResourceMembershipLinks
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    url_id TEXT
);
CREATE TABLE OptimizationResults
(
    customer_member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    resource_member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    time_start timestamp
);
