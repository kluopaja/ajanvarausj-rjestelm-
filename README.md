# Ajanvarausjärjestelmä

Aineopintojen harjoitustyö: Tietokantasovellus

Ajanvarausjärjestelmä, joka pyrkii maksimoimoimaan onnistuneiden varauksien ja käyttäjien tyytyväisyyden määrän. 

Tämänhetkinen tilanne:

Käyttäjät pystyvät rekisteröitymään ja kirjautumaan sovellukseen.

Kirjautuneet käyttäjät voivat luoda kyselyitä. Kyselyn luoneesta käyttäjästä tulee kyselyn omistaja, jolla on muita laajemmat valtuudet hallinnoida kyselyä.

Omistaja pystyy luomaan kyselyihin varattavia resursseja. Resurssit ovat tällä hetkellä kaikki identtisiä (esim. voisi vastata montaa identtistä huonetta). 

Omistaja voi myös luoda kyselyyn linkkejä, joilla pystyy kutsumaan muita kirjautuneita käyttäjiä varaamaan halutun pituisia aikoja kyselystä. Linkeillä voi kutsua myös muita käyttäjiä hallinnoimaan kyselyn resurssien saatavuutta. Tällä hetkellä kyselyn omistajankin pitää vierailla kyselylinkeissä lisätäkseen itsensä näihin toimintoihin.

Kyselyyn vastaajaksi kutsuttu käyttäjä voi määritellä itselleen sopivat ajat ja näillä arvot "sopii tarvittaessa" ja "sopii hyvin".

Tällä hetkellä aikatoiveiden katselemisen ja päivittämisen käytettävyys on hyin heikko, mutta tätä olisi tarkoitus parantaa seuraavaa välipalautusta varten.

Kyselyn omistaja voi myös optimoida ajanvaraukset, jolloin sovellus pyrkii jakamaan kyselyn resursseja kyselyyn vastanneiden käyttäjille käyttäjiden toiveet huomioiden.

