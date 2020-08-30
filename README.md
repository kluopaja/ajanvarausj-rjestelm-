# Ajanvarausjärjestelmä

Aineopintojen harjoitustyö: Tietokantasovellus

Ajanvarausjärjestelmä, joka pyrkii maksimoimoimaan onnistuneiden varauksien ja 
käyttäjien tyytyväisyyden määrän. 

Sivu on jaoteltu käyttäjien (user) luomiin kyselyihin (poll). Kyselyn luoneesta
käyttäjästä tulee samalla kyselyn omistaja (owner). Jokaisella
kyselyllä on jäseniä (member). Jäsenet voivat olla joko tyyppiä varaaja/asiakas 
(customer) tai tyyppiä resurssi (resource). 

Kyselyn luomisen lisäksi käyttäjät voivat hallinnoida kyselyiden jäseniä. 
Jokaista jäsentä voi hallinnoida samaan aikaan usea eri käyttäjä.
Oletuksena kyselyn omistajalla on oikeudet hallinnoida kaikkia jäseniä.

Asiakastyyppistä jäsentä hallinnoiva käyttäjä voi asettaa asiakkaalle 
aikatoiveita (time grades). Aikatoive kuvaa jäsenen mielipidettä siitä, kuinka
mielellään hän milläkin ajanhetkellä haluaisi käyttää kyselyn resursseja.
Aikatoiveiden tyypit ovat tällä hetkellä:
* Ei sovi
* Sopii tarvittaessa
* Sopii hyvin

Resurssityyppistä jäsentä hallinnoiva käyttäjä voi asettaa resurssille
saatavuustietoja (koodissa myös nämä time grades). Resurssin saatavuustiedot
kertovat sen, milloin resurssi on asiakkaiden käytettävissä. Saatavuustietojen
tyypit ovat tällä hetkellä:
* Ei käytettävissä
* Käytettävissä

Kyselyn omistaja voi suorittaa aikatoiveiden optimoinnin (optimization), jolloin
sivusto pyrkii jakamaan resurssit niiden saatavuuden rajoissa asiakkaille siten,
että mahdollisimman moni asiakas pystyisi käyttämään resurssia toivomaansa
aikaan. (Tietyllä ajanhetkellä jokainen resurssi voi olla vain yhden asiakkaan
käytössä.)

Kyselyn omistaja voi luoda kyselyyn uusia asiakkaita ja resursseja. Uuden 
asiakkaan luomisen yhteydessä kyselyn omistaja määrittää, kuinka pitkän ajan
kyseinen asiakas haluaa varata.

Uuden asiakkaan tai resurssin luomisen jälkeen kyselyn omistaja voi generoida
muokkauslinkkejä (member access link). Muokkauslinkkejä voidaan käyttää
kutsumaan muita käyttäjiä
kyselyyn hallinnoimaan tietyn asiakkaan tai resurssin aikoja.

Tämän lisäksi omistaja voi luoda uuden asiakkaan luomieen oikeuttavia linkkejä
(new customer link).
Näitä linkkejä painamalla käyttäjä voi luoda uusia asiakkaita ja määrittää
samalla asiakkaan varausajan pituuden.

## Ajanvarauskyselyn kulku

Ajanvarauskysely voi olla kolmessa eri tilassa
* Käynnissä (0, running)
* Odottaa tuloksia (1, ended)
* Tulokset julkaistu (2, results)

Kysely on oletuksena tilassa 0. Kun kyselyn loppumisaika siirtyy menneisyyteen, 
siirtyy kysely tilaan 1. Kyselyn omistaja voi halutessaan siirtää kyselyn 
loppumisajan nykyseen hetkeen (== lopettaa kyselyn). Omistaja voi myös
siirtää kyselyn loppumishetken tulevaisuuteen. Tällöin kysely siirtyy
automaattisesti tilaan 1 (ellei jo ollut siinä). 

Tilassa 1 kysely toimii omistajan näkökulmasta täysin normaalisti (eli 
omistaja voi luoda uusia asiakkaita/resursseja ja muokata niiden aikoja
yms). Muuttamalla kyselyn loppuhetken takaisin tulevaisuuteen
voi omistaja siirtää kyselyn takaisin tilaan 0. 
Kuitenkin linkit lakkaavat toimimasta. (Tällä hetkellä hieman
epäloogisesti uuden käyttäjän luomiseen oikeuttavat linkit lakkaavat
toimimasta myös kyselyn omistajan käyttäessä niitä. Omistaja voi 
kuitenkin aina luoda uusia asiakkaita "Asiakkaat"-viulla.)

Tavalliset käyttäjät voivat tilassa 1 ainoastaan tarkastella
heidän jo tekemiänsä aikatoiveita.

Tilassa 1 omistaja voi lisäksi julkaista kyselyn tulokset. Tulosten 
julkaiseminen on peruuttamaton toiminto ja siirtää kyselyn tilaan 2. 
Tilassa 2 kukaan ei voi enää muokata kyselyn tuloksia. Tilassa 2
"Tulokset" sivulle tulee näkyviin kyselyn lopulliset tulokset.
Tavalliset käyttäjät näkevät ainoastaan ne tulokset, joihin heillä
on oikeudet, mutta omistaja näkee kaikki tulokset.



## Lisää muokkauslinkeistä ja käyttäjäluontilinkeistä:

Tällä hetkellä kyselyn oikeuksien hallinta perustuu kahdenlaiseen
käyttäjäskenaarioon.


### Epäluotettavat käyttäjät
Kyselyn omistaja ei luota kyselyyn vastaaviin käyttäjiin. Tällöin käyttäjille
ei haluta antaa liikaa oikeuksia kuten mahdollisuutta luoda mielivaltainen 
määrä uusia asiakkaita.

Nyt kyselyn omistaja luo kyselyyn asiakkaita halutuilla varauspituuksilla.
Tämän jälkeen omistaja luo muokkauslinkit asiakkaille ja jakaa muokkauslinkit
turvallista väylää pitkin käyttäjille.

Jos nyt yksi käyttäjistä osoittautuu epäluotettavaksi tai ei esimerkiksi osaa
käyttää sivua oikein, rajoittuu vahinko vain yhden asiakkaan aikoihin.

### Luotettavat käyttäjät

Kyselyn omistaja luottaa kyselyyn vastaaviin käyttäjiin. Tällöin omistaja voi 
luoda kyselyyn käyttäjäluontilinkin. Omistaja voi sitten helposti jakaa tämän
käyttäjäluontilinkin esimerkiksi yksityisessä keskusteluryhmässä.

Linkissä vierailevat käyttäjä voivat sitten luoda asiakkaita kyselyyn valiten
itse luomiensa asiakkaiden varausaikojen pituudet.

## Tunnettuja ongelmia ja vielä työn alla olevia asioita


* Aikatoiveiden ja resurssien saatavuuden valiseminen toimii huonosti
  kosketusnäytöllä.
* Käyttäjän aikavyöhykettä ei oteta sovelluksessa mitenkään huomioon
* Kyselyn päättymisajan muokkausta ei tarkisteta javascriptillä

## Sovelluksen testaaminen
Sovellusta voi testata osoitteessa https://csos.herokuapp.com/
Testikäyttäjiä ovat esim: (maija, kissa2) (tiina, kissa2)
