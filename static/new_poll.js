let poll_name = document.getElementById("poll_name");
let poll_description = document.getElementById("poll_description");
let first_appointment_date = document.getElementById("first_appointment_date");
let last_appointment_date = document.getElementById("last_appointment_date");
let poll_end_date = document.getElementById("poll_end_date");
let poll_end_time = document.getElementById("poll_end_time");

let form = document.querySelector("form");
let name_error = document.getElementById("name_error");
let description_error = document.getElementById("description_error");
let first_date_error = document.getElementById("first_date_error");
let last_date_error = document.getElementById("last_date_error");
let end_date_error = document.getElementById("end_date_error");
let end_time_error = document.getElementById("end_time_error");

let date_relations_error = document.getElementById("date_relations_error");
let datetime_error = document.getElementById("datetime_error");

poll_name.addEventListener("input", check_name);
poll_description.addEventListener("input", check_description);
first_appointment_date.addEventListener("input", () => {
    check_first();
    check_date_relations();
});
last_appointment_date.addEventListener("input", () => {
    check_last();
    check_date_relations();
});
poll_end_date.addEventListener("input", () => {
    check_end_datetime();
    check_date_relations();
});
poll_end_time.addEventListener("input", check_end_datetime);

form.addEventListener("submit", function (event) {
    if(!(check_name() && check_description() && check_first() && check_last() &&
         check_end_date() && check_end_time())) {
        event.preventDefault();
        alert("Virhe! Tarkista syötteiden oikeellisuus.");
    }
});


function check_name() {
    let name = poll_name.value
    let name_ok = true;
    name_error.textContent = "";
    if(name.length == 0) {
        name_error.textContent = "Nimi ei voi olla tyhjä";
        return false;
    }
    if(name.length > 30) {
        name_error.textContent = "Nimi liian pitkä";
        return false;
    }
    return true;
}
function check_description() {
    let description = poll_description.value;
    let desc_ok = true;
    description_error.textContent = "";
    console.log(description.length);
    if(description.length == 0) {
        description_error.textContent = "Kyselyn kuvaus ei voi olla tyhjä"
        return false;
    }
    if(description.length > 10000) {
        description_error.textContent = "Kyselyn kuvaus liian pitkä (yli 10 000 merkkiä)"
        return false;
    }
    return true;
}
function check_first() {
    let date = first_appointment_date.value;
    if(check_date(date, first_date_error)) {
        return false;
    }
    return true;
}
function check_last() {
    let date = last_appointment_date.value;
    if(check_date(date, last_date_error)) {
        return false;
    }
    return true;
}
function check_end_datetime() {
    if(!(check_end_date() && check_end_time())) {
        return false;
    }
    //TODO checki if datetime is in the past
    return true;
}
function check_end_date() {
    let date = poll_end_date.value;
    if(check_date(date, end_date_error)) {
        return false;
    }
    return true;
}
function check_end_time() {
    let time = poll_end_time.value;
    let regex = RegExp("^(([0-1][0-9])|(2[0-3])):[0-5][0-9]$");
    end_time_error.textContent = "";
    if(!regex.test(time)) {
        let tmp = "Virheellinen aika. Syötä aika 24 tunnin formaatissa HH:MM."
        end_time_error.textContent = tmp;
        return false;
    }
    let mins = time.substring(4, 5);
    if(parseInt(mins)%5 != 0) {
        tmp = "Minuuttien tulee olla viidellä jaollisia"
        end_time_error.textContent = tmp;
        return false;
    }
    return true;
}
//NOTE that this also accepts dates with time which should not be the case
function check_date(d, error_element) {
    let date = new Date(d)
    error_element.textContent = "";
    if(!is_valid_date(date)) {
        let tmp = "Päivämäärän formaatti on väärä. Oikea formaatti riippuu selaimestasi. Vanhoilla selaimilla kannattaa koittaa YYYY-MM-DD.";
        error_element.textContent = tmp;
        return false;
    }
    return true;
}
function is_valid_date(d) {
    return d instanceof Date && !isNaN(d);
}
//checks if the dates are correct relative to other dates
//i.e. some dates are before others etc
function check_date_relations() {
    let first_date = new Date(first_appointment_date.value);
    let last_date = new Date(last_appointment_date.value);
    let end_date = new Date(poll_end_date.value);
    date_relations_error.textContent = "";
    //Proceed only if all of the dates are valid
    if(!(is_valid_date(first_date) && is_valid_date(last_date) &&
         is_valid_date(end_date))) {
        return false;
    }
    //Convert to milliseconds since epoch
    first_date = first_date.getTime();
    last_date = last_date.getTime();
    end_date = end_date.getTime();
    console.log(first_date, last_date, end_date);
    if(first_date > last_date) {
        let tmp = "Ensimmäisen varauspäivän tulee olla ennen viimeistä varauspäivää";
        date_relations_error.textContent = tmp;
        return false;
    }
    let poll_days = (last_date-first_date)/1000/60/60/24 + 1;
    if(poll_days > 31) {
        let tmp = "Kyselyssä voi olla korkeintaan 31 varauspäivää";
        date_relations_error.textContent = tmp;
        return false;
    }
    return true;
}
