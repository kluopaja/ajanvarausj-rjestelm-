let pollName = document.getElementById("poll_name");
let pollDescription = document.getElementById("poll_description");
let firstAppointmentDate = document.getElementById("first_appointment_date");
let lastAppointmentDate = document.getElementById("last_appointment_date");
let pollEndDate = document.getElementById("poll_end_date");
let pollEndTime = document.getElementById("poll_end_time");

let form = document.querySelector("form");
let nameError = document.getElementById("name_error");
let descriptionError = document.getElementById("description_error");
let firstDateError = document.getElementById("first_date_error");
let lastDateError = document.getElementById("last_date_error");
let endDateError = document.getElementById("end_date_error");
let endTimeError = document.getElementById("end_time_error");

let dateRelationsError = document.getElementById("date_relations_error");
let datetimeError = document.getElementById("datetime_error");

pollName.addEventListener("input", checkName);
pollDescription.addEventListener("input", checkDescription);
firstAppointmentDate.addEventListener("input", () => {
    checkFirst();
    checkDateRelations();
});
firstAppointmentDate.addEventListener("keyup", () => {
    checkFirst();
    checkDateRelations();
});
lastAppointmentDate.addEventListener("input", () => {
    checkLast();
    checkDateRelations();
});
lastAppointmentDate.addEventListener("keyup", () => {
    checkLast();
    checkDateRelations();
});
pollEndDate.addEventListener("input", () => {
    checkEndDate();
    checkDateRelations();
});
pollEndDate.addEventListener("keyup", () => {
    checkEndDate();
    checkDateRelations();
});
pollEndTime.addEventListener("input", checkEndTime);
form.addEventListener("submit", function (event) {
    if(!(checkName() && checkDescription() && checkFirst() && checkLast() &&
         checkEndDate() && checkEndTime())) {
        event.preventDefault();
        alert("Virhe! Tarkista syötteiden oikeellisuus.");
    }
});

function checkName() {
    let name = pollName.value
    let nameOk = true;
    nameError.textContent = "";
    if(name.length == 0) {
        nameError.textContent = "Nimi ei voi olla tyhjä";
        return false;
    }
    if(name.length > 30) {
        nameError.textContent = "Nimi liian pitkä";
        return false;
    }
    return true;
}
function checkDescription() {
    let description = pollDescription.value;
    let descOk = true;
    descriptionError.textContent = "";
    if(description.length == 0) {
        descriptionError.textContent = "Kyselyn kuvaus ei voi olla tyhjä"
        return false;
    }
    if(description.length > 10000) {
        descriptionError.textContent = "Kyselyn kuvaus liian pitkä (yli 10 000 merkkiä)"
        return false;
    }
    return true;
}
function checkFirst() {
    let date = firstAppointmentDate.value;
    if(!checkDate(date, firstDateError)) {
        return false;
    }
    return true;
}
function checkLast() {
    let date = lastAppointmentDate.value;
    if(!checkDate(date, lastDateError)) {
        return false;
    }
    return true;
}
function checkEndDate() {
    let date = pollEndDate.value;
    if(!checkDate(date, endDateError)) {
        return false;
    }
    return true;
}
function checkEndTime() {
    let time = pollEndTime.value;
    let regex = RegExp("^(([0-1][0-9])|(2[0-3])):[0-5][0-9]$");
    endTimeError.textContent = "";
    if(!regex.test(time)) {
        let tmp = "Virheellinen aika. Syötä aika 24 tunnin formaatissa HH:MM."
        endTimeError.textContent = tmp;
        return false;
    }
    let mins = time.substring(4, 5);
    return true;
}
//NOTE that this also accepts dates with time which should not be the case
function checkDate(d, errorElement) {
    let date = new Date(d)
    errorElement.textContent = "";
    if(!isValidDate(date)) {
        let tmp = "Päivämäärän formaatti on väärä. Oikea formaatti riippuu selaimestasi. Vanhoilla selaimilla kannattaa koittaa YYYY-MM-DD.";
        errorElement.textContent = tmp;
        return false;
    }
    return true;
}
function isValidDate(d) {
    return d instanceof Date && !isNaN(d);
}
//checks if the dates are correct relative to other dates
//i.e. some dates are before others etc
function checkDateRelations() {
    let firstDate = new Date(firstAppointmentDate.value);
    let lastDate = new Date(lastAppointmentDate.value);
    let endDate = new Date(pollEndDate.value);
    dateRelationsError.textContent = "";
    //Proceed only if all of the dates are valid
    if(!(isValidDate(firstDate) && isValidDate(lastDate) &&
         isValidDate(endDate))) {
        return false;
    }
    //Convert to milliseconds since epoch
    firstDate = firstDate.getTime();
    lastDate = lastDate.getTime();
    endDate = endDate.getTime();
    if(firstDate > lastDate) {
        let tmp = "Ensimmäisen varauspäivän tulee olla ennen viimeistä varauspäivää";
        dateRelationsError.textContent = tmp;
        return false;
    }
    let pollDays = (lastDate-firstDate)/1000/60/60/24 + 1;
    if(pollDays > 31) {
        let tmp = "Kyselyssä voi olla korkeintaan 31 varauspäivää";
        dateRelationsError.textContent = tmp;
        return false;
    }
    return true;
}
