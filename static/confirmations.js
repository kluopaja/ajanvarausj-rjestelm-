addConfirmationToElements= function(cls, message) {
    let v = document.querySelectorAll(cls)
    for(let i = 0; i < v.length; i++) {
        v[i].addEventListener('submit', e => {
            if(!confirm(message)) {
                e.preventDefault()
            }
        });
    }
}
handleWindowLoad = function() {
    addConfirmationToElements(".delete_customer",
                              "Haluatko varmasti poistaa asiakkaan?")
    addConfirmationToElements(".delete_member_access_link",
                              "Haluatko varmasti poistaa asikkaanmuokkauslinkin?")
    addConfirmationToElements(".delete_new_customer_link",
                              "Haluatko varmasti poistaa asiakkaanluontilinkin?")
    addConfirmationToElements(".delete_resource",
                              "Haluatko varmasti poistaa resurssin?")

    addConfirmationToElements(".delete_resource_access_link",
                              "Haluatko varmasti poistaa resurssinmuokkauslinkin?")

    addConfirmationToElements(".optimize_poll",
                             "Haluatko varmasti optimoida ajanvaraukset? \
Optimoiminen ylikirjoittaa vanhat tulokset")

    addConfirmationToElements(".set_results_final",
                              "Haluatko varmasti julkaista optimoinnin \
tulokset? Tätä operaatioita ei voi peruuttaa")
    }
window.addEventListener('load', (e) => {
    handleWindowLoad()
})
