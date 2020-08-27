//TODO add event linsteners to register.html
let username = document.getElementById("username");
let password = document.getElementById("password");
let confirmPassword = document.getElementById("confirm_password");
let form = document.querySelector("form")
let usernameError = document.getElementById("username_error")
let passwordError = document.getElementById("password_error")
let confirmError = document.getElementById("confirm_error")

username.addEventListener("keyup", function (event) {
    checkUsername();
});
password.addEventListener("keyup", function (event) {
    checkPassword();
});
confirmPassword.addEventListener("keyup", function (event) {
    checkPassword();
})

form.addEventListener("submit", function (event) {
    if(!(checkUsername() && checkPassword())) {
        event.preventDefault();
        alert("Virhe! Tarkista syötteiden oikeellisuus.")
    } 
});


function checkUsername() {
    let username = document.getElementById("username")
    regex = RegExp("^[a-zA-Z0-9]+$")

    usernameError.textContent = "";
    if(!regex.test(username.value)) {
        usernameError.textContent = "Käyttäjänimi ei kelpaa.";
        return false;
    }
    return true;
}
function checkPassword() {

    passwordOk = true;
    passwordError.textContent = "";
    confirmError.textContent = "";
    if(password.value.length == 0) {
        passwordError.textContent = "Salasana ei voi olla tyhjä.";
        passwordOk = false;
    }
    if(password.value != confirmPassword.value) {
        confirmError.textContent = "Salasanat eivät täsmää.";
        passwordOk = false;
    }
    return passwordOk;
}
