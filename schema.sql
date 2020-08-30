CREATE TABLE Users
(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);
CREATE TABLE Polls
(
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES Users (id) ON DELETE CASCADE,
    name TEXT,
    description TEXT,
    first_appointment_date date,
    last_appointment_date date,
    end_time timestamp, --change name?
    has_final_results boolean,
    CHECK(first_appointment_date <= last_appointment_date)
);
CREATE TABLE PollMembers
(
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES Polls (id) ON DELETE CASCADE,
    name TEXT
);
CREATE TABLE MemberTimeGrades
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    --half open intervals [time_beginning, time_end)
    time_beginning timestamp,
    time_end timestamp,
    grade INTEGER
);
CREATE TABLE Customers
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    reservation_length interval
);
CREATE TABLE Resources
(
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
    times_used INTEGER DEFAULT 0,
    url_key TEXT
);
CREATE TABLE MemberAccessLinks
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    url_key TEXT
);
CREATE TABLE OptimizationResults
(
    customer_member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    resource_member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    time_start timestamp
);
