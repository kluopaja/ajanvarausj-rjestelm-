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
    *Ei sovi
    *Sopii tarvittaessa
    *Sopii hyvin

Resurssityyppistä jäsentä hallinnoiva käyttäjä voi myös asettaa resurssille
saatavuustietoja (koodissa myös nämä time grades). Resurssin saatavuustiedot
kertovat sen, milloin resurssi on asiakkaiden käytettävissä. Saatavuustietojen
tyypit ovat tällä hetkellä:
    *Ei käytettävissä
    *Käytettävissä

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

* Tällä hetkellä vain kyselyn omistaja voi katsoa kyselyn aikojen optimoinnin
tuloksia.
  * Tarkoitus olisi, että jokainen käyttäjä voisi tarkastella omille
    kyselyjäsenillensä optimoituja aikoja.
* Edelliseen liittyen kyselyn loppumisajankohta ei tee tällä hetkellä mitään.
  * Tarkoitus olisi, että loppumisajankohdan jälkeen ajanvarauksia voisi
    muokata pelkästään kyselyn omistaja
* Optimoinnin tulosten formaattia tulisi vielä parantaa helppolukuisemmaksi.
* Kapealla näytöllä (esim. mobiililaitteet) osa sivuston sisällöstä jää näytön 
  ulkopuolelle
* Aikatoiveiden ja resurssien saatavuuden valiseminen toimii huonosti
  kosketusnäytöllä.
* Käyttäjän aikavyöhykettä ei oteta sovelluksessa mitenkään huomioon
* Tietokannan rakenne vaatii vielä miettimistä
  * Resources-taulussa oli aiemmin sarake "resource_name", joka siirrettiin
    PollMembers-tauluun. Tällä hetkellä olisi varmaankin järkevämpää poistaa
    Resources-taulu (ja mahdollisesti Customers) taulu kokonaan ja siirtää
    tieto PollMembers-tauluun. Toisaalta tulevaisuudessa resursseille ja
    asiakkaille olisi mukava pystyä asettamaan ominaisuuksia, kuten
    "sallittujen yhtäaikaisten asiakkaiden määrä" (resurssille) ja
    "haluttujen varausaikojen määrä" (asiakkaalle). Mielestäni tämä puoltaa 
    nykyisen tietokantarakenteen säilyttämistä.

## Sovelluksen testaaminen
Sovellusta voi testata osoitteessa https://boiling-falls-99919.herokuapp.com/
