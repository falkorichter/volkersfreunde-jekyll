---
title: "mailman – tipps"
date: 2021-04-01 08:32:17 +0000
permalink: /mailman-tipps/
author: "Falko"
categories: ["Allgemein"]
tags: []
wp_id: 2538
---
### Wenn man Mailingliste für externe zugänglich machen will:

unter `/mailman/admin/<deine-liste>/privacy/sender`

**Alle Absender akzeptieren**

> Aktion, die beim Eingang einer Nachricht eines Nichtmitgliedes ausgeführt werden soll, wenn für dieses Nichtmitglied bislang keine Aktion hinterlegt ist. (Details zu generic_nonmember_action)

auf *Akzeptieren* setzen

**Antwort An: einstellen (damit immer an die Liste geantwortet wird)**

> An welche Adresse sollen die Antworten auf Nachrichten der Liste gesendet werden? Absender wird dringend empfohlen für die meisten Mailinglisten.(Details zu reply_goes_to_list)

auf *This list and Poster* setzen. Oder bei internen Listen auf *Diese Liste*.

> Sollen vorhandene Reply-To:-Header der Orginal-Nachricht verworfen werden? Falls diese Option aktiviert ist, wird der Header auch dann entfernt, wenn kein explizierter Reply-To:-Header der Liste gesetzt ist.  
> (Details zu first_strip_reply_to)

auf *Ja* setzen. Auch hier damit die Antworten immer in der Liste landen.

unter `/mailman/admin/<deine-liste>/privacy/recipient`

Wenn man die Liste hinter einer Weiterleitung verstecken will:

> Nachrichten an die Liste müssen exakt an die Listen-Mail-Adresse (oder an einen der unten einstellbaren Aliasnamen) adressiert sein (‘To:’, ‘Cc’).  
> (Details zu require_explicit_destination)

