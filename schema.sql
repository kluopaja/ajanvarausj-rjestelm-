CREATE TABLE Users
(
    user_id SERIAL PRIMARY KEY,
    username TEXT,
    password_hash TEXT --should this be something else than TEXT?
);
CREATE TABLE Polls
(
    poll_id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES Users (user_id) ON DELETE CASCADE, --Also there was ON UPDATE CASCADE, check these!
    poll_name TEXT,
    poll_description TEXT,
    first_appointment_date date,
    last_appointment_date date,
    poll_end_time timestamp, --change name?
    has_final_results boolean
);
CREATE TABLE PollMembers
(
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES Polls (poll_id) ON DELETE CASCADE
);
CREATE TABLE MemberTimeSelections
(
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    --half open intervals [time_beginning, time_end)
    time_beginning timestamp,
    time_end timestamp,
    satisfaction INTEGER
);
CREATE TABLE UsersPollMembers
(
    user_id INTEGER REFERENCES Users (user_id) ON DELETE CASCADE,
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE,
    reservation_length interval
);
CREATE TABLE Resources
(
    resource_id SERIAL PRIMARY KEY,
    resource_description TEXT, --Should have a unique name/description
    member_id INTEGER REFERENCES PollMembers (id) ON DELETE CASCADE 
    --TODO rename to parent_poll_id
);
CREATE TABLE UsersResources
(
    user_id INTEGER REFERENCES Users (user_id) ON DELETE CASCADE,
    resource_id INTEGER REFERENCES Resources (resource_id) ON DELETE CASCADE
);
CREATE TABLE PollMembershipLinks
(
    poll_id INTEGER REFERENCES Polls (poll_id) ON DELETE CASCADE,
    url_id TEXT,
    reservation_length interval
);
CREATE TABLE ResourceMembershipLinks
(
    resource_id INTEGER REFERENCES Resources (resource_id) ON DELETE CASCADE,
    url_id TEXT
);
CREATE TABLE OptimizationResults
(
    poll_id INTEGER REFERENCES Polls (poll_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES Users (user_id) ON DELETE CASCADE,
    appointment_start timestamp
);
