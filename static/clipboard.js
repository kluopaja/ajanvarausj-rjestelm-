copyToClipboard = function(e) {
    let url = document.getElementById(e.target.id)
    url.select()
    document.execCommand("copy")
    alert("Kopioitu leikepöydälle: " + url.value)
}
window.addEventListener('load', (e) => {
    let buttons = document.querySelectorAll(".copy_button")
    for(let i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', copyToClipboard);
    }
});



