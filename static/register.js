//TODO add event linsteners to register.html
let username = document.getElementById("username");
let password = document.getElementById("password");
let confirm_password = document.getElementById("confirm_password");
let form = document.querySelector("form")
let username_error = document.getElementById("username_error")
let password_error = document.getElementById("password_error")
let confirm_error = document.getElementById("confirm_error")

username.addEventListener("keyup", function (event) {
    check_username();
});
password.addEventListener("keyup", function (event) {
    check_password();
});
confirm_password.addEventListener("keyup", function (event) {
    check_password();
})

form.addEventListener("submit", function (event) {
    if(!(check_username() && check_password())) {
        event.preventDefault();
        alert("Virhe! Tarkista syötteiden oikeellisuus.")
    } 
});


function check_username() {
    let username = document.getElementById("username")
    regex = RegExp("^[a-zA-Z0-9]+$")

    username_error.textContent = "";
    if(!regex.test(username.value)) {
        username_error.textContent = "Käyttäjänimi ei kelpaa.";
        return false;
    }
    return true;
}
function check_password() {

    password_ok = true;
    password_error.textContent = "";
    confirm_error.textContent = "";
    if(password.value.length == 0) {
        password_error.textContent = "Salasana ei voi olla tyhjä.";
        password_ok = false;
    }
    if(password.value != confirm_password.value) {
        confirm_error.textContent = "Salasanat eivät täsmää.";
        password_ok = false;
    }
    return password_ok;
}
